-- Household Electricity Dashboard: MySQL triggers & procedures
-- Save this file and run it in the same database/schema used by Django
-- Adjust `price_per_kwh` below if required.

DELIMITER $$

/* --------------------------------------------------------------------------
   Config: change this value to reflect your local price per kWh (MUR)
   You can also pass a price parameter to recompute_monthly_usage if desired.
   -------------------------------------------------------------------------- */
SET @price_per_kwh = 5.0; -- MUR per kWh (change as needed)

/* --------------------------------------------------------------------------
   Procedure: recompute_monthly_usage(appliance_id, year, month)
   Computes totals for a single appliance and upserts the monthly row.
   Uses @price_per_kwh unless a different price is supplied via a parameter.
   -------------------------------------------------------------------------- */
DROP PROCEDURE IF EXISTS recompute_monthly_usage $$
CREATE PROCEDURE recompute_monthly_usage(
  IN in_appliance_id INT,
  IN in_year INT,
  IN in_month INT,
  IN in_price_per_kwh DOUBLE DEFAULT NULL
)
BEGIN
  DECLARE total_hours DOUBLE DEFAULT 0;
  DECLARE power_rating DOUBLE DEFAULT 0;
  DECLARE threshold_hours DOUBLE DEFAULT 0;
  DECLARE resident_id INT DEFAULT NULL;
  DECLARE user_id INT DEFAULT NULL;
  DECLARE days_in_month INT DEFAULT 0;
  DECLARE total_energy DOUBLE DEFAULT 0;
  DECLARE total_cost DOUBLE DEFAULT 0;
  DECLARE avg_daily DOUBLE DEFAULT 0;
  DECLARE used_price DOUBLE DEFAULT 0;

  SET used_price = COALESCE(in_price_per_kwh, @price_per_kwh, 5.0);

  -- Ensure target table exists; if not, exit quietly
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
     WHERE table_schema = DATABASE() AND table_name = 'dashboard_monthlyapplianceusage'
  ) THEN
    SIGNAL SQLSTATE '01000' SET MESSAGE_TEXT = 'Target table dashboard_monthlyapplianceusage does not exist';
  END IF;

  -- Aggregate hours for appliance/month
  SELECT COALESCE(SUM(hours_used),0) INTO total_hours
    FROM dashboard_usagerecord
   WHERE appliance_id = in_appliance_id
     AND YEAR(`date`) = in_year
     AND MONTH(`date`) = in_month;

  -- appliance metadata
  SELECT power_rating, threshold_hours, resident_id
    INTO power_rating, threshold_hours, resident_id
    FROM dashboard_appliance
   WHERE id = in_appliance_id
   LIMIT 1;

  IF resident_id IS NOT NULL THEN
    SELECT user_id INTO user_id FROM dashboard_resident WHERE id = resident_id LIMIT 1;
  END IF;

  SET days_in_month = DAY(LAST_DAY(CONCAT(in_year,'-',LPAD(in_month,2,'0'),'-01')));
  SET total_energy = total_hours * power_rating / 1000;
  SET total_cost = total_energy * used_price;
  SET avg_daily = IF(days_in_month > 0, total_hours / days_in_month, 0);

  -- Create unique index if it doesn't exist (idempotent)
  SELECT COUNT(*) INTO @idx_count
    FROM information_schema.statistics
   WHERE table_schema = DATABASE()
     AND table_name = 'dashboard_monthlyapplianceusage'
     AND index_name = 'idx_monthly_appliance_year_month';

  IF @idx_count = 0 THEN
    SET @s = 'CREATE UNIQUE INDEX idx_monthly_appliance_year_month ON dashboard_monthlyapplianceusage (appliance_id, year, month)';
    PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
  END IF;

  -- Upsert the aggregated row
  INSERT INTO dashboard_monthlyapplianceusage
    (appliance_id, year, month, total_hours, total_energy_kwh, total_cost, avg_daily_hours, threshold_exceeded, user_id, resident_id, created_at, updated_at)
  VALUES
    (in_appliance_id, in_year, in_month, total_hours, total_energy, total_cost, avg_daily, IF(avg_daily > threshold_hours, 1, 0), user_id, resident_id, NOW(), NOW())
  ON DUPLICATE KEY UPDATE
    total_hours = VALUES(total_hours),
    total_energy_kwh = VALUES(total_energy_kwh),
    total_cost = VALUES(total_cost),
    avg_daily_hours = VALUES(avg_daily_hours),
    threshold_exceeded = VALUES(threshold_exceeded),
    updated_at = NOW();

END $$

/* --------------------------------------------------------------------------
   Procedure: recompute_month_for_month(year, month)
   Recomputes monthly entries for all appliances (useful after bulk imports).
   -------------------------------------------------------------------------- */
DROP PROCEDURE IF EXISTS recompute_month_for_month $$
CREATE PROCEDURE recompute_month_for_month(
  IN in_year INT,
  IN in_month INT,
  IN in_price_per_kwh DOUBLE DEFAULT NULL
)
BEGIN
  DECLARE done INT DEFAULT FALSE;
  DECLARE a_id INT;
  DECLARE cur CURSOR FOR SELECT id FROM dashboard_appliance;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO a_id;
    IF done THEN
      LEAVE read_loop;
    END IF;
    CALL recompute_monthly_usage(a_id, in_year, in_month, in_price_per_kwh);
  END LOOP;
  CLOSE cur;
END $$

-- Remove existing triggers if present (safe to run multiple times)
DROP TRIGGER IF EXISTS trg_usagerecord_after_insert $$
DROP TRIGGER IF EXISTS trg_usagerecord_after_delete $$
DROP TRIGGER IF EXISTS trg_usagerecord_after_update $$

/* AFTER INSERT: update the newly affected month */
CREATE TRIGGER trg_usagerecord_after_insert
AFTER INSERT ON dashboard_usagerecord
FOR EACH ROW
BEGIN
  CALL recompute_monthly_usage(NEW.appliance_id, YEAR(NEW.`date`), MONTH(NEW.`date`));
END $$

/* AFTER DELETE: update the month that lost a record */
CREATE TRIGGER trg_usagerecord_after_delete
AFTER DELETE ON dashboard_usagerecord
FOR EACH ROW
BEGIN
  CALL recompute_monthly_usage(OLD.appliance_id, YEAR(OLD.`date`), MONTH(OLD.`date`));
END $$

/* AFTER UPDATE: recompute both old and new months (handles appliance/date change) */
CREATE TRIGGER trg_usagerecord_after_update
AFTER UPDATE ON dashboard_usagerecord
FOR EACH ROW
BEGIN
  CALL recompute_monthly_usage(OLD.appliance_id, YEAR(OLD.`date`), MONTH(OLD.`date`));
  CALL recompute_monthly_usage(NEW.appliance_id, YEAR(NEW.`date`), MONTH(NEW.`date`));
END $$

DELIMITER ;

-- Usage notes:
-- 1) To run a bulk recompute for Feb 2026: CALL recompute_month_for_month(2026,2);
-- 2) To recompute a specific appliance/month: CALL recompute_monthly_usage(1,2026,2);
-- 3) Change @price_per_kwh at top if you need a different rate.
