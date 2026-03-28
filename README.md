# Household Electricity Consumption Dashboard

This project is a professional web-based dashboard for monitoring household electricity consumption. It allows users to register, log in, and manage their appliances and usage records. The dashboard provides visualizations of energy usage, trend analysis, warning alerts, and options for exporting data.

## Features

- User authentication (login with username: VIK, password: VB1234)
- Database models for Appliances, Usage Records, and Alerts
- Preloaded sample datasets for common appliances and usage records
- Interactive charts for energy usage visualization
- Trend analysis with weekly comparisons
- Smart alerts for high energy usage
- **Critical Appliances Management** - Identify and monitor appliances requiring digital meters
- Data export options in CSV and PDF formats
- Professional responsive UI with dark/light theme
- Energy saving tips and recommendations

## Critical Appliances & Digital Meter Monitoring

The system now includes advanced functionality to identify and manage critical appliances that require digital meter monitoring:

### Key Features:
- **Critical Appliance Identification**: Mark appliances that need digital monitoring
- **Priority Levels**: Set monitoring priority (Low, Medium, High)
- **Smart Suggestions**: AI-powered recommendations for appliances that should be critical
- **Digital Meter Planning**: Tools to plan and track digital meter installations
- **Usage-Based Analysis**: Automatic detection based on power consumption and usage patterns

### How to Use:
1. **View Critical Appliances**: Navigate to "Critical Appliances" in the menu
2. **Mark as Critical**: Use the interface to mark appliances requiring digital meters
3. **Set Priorities**: Assign priority levels for monitoring importance
4. **Review Suggestions**: Check AI recommendations for appliances to monitor
5. **Plan Installation**: Use the installation guide for digital meter setup

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Create Default User:**
   ```bash
   python manage.py create_default_user
   ```
   This creates a user with username "VIK" and password "VB1234".

4. **Load Sample Data (Optional):**
   ```bash
   python manage.py loaddata dashboard/fixtures/appliances.json
   python manage.py loaddata dashboard/fixtures/usage_records.json
   ```

5. **Configure Email (Optional - Per Profile):**
   **No global email configuration needed!** Each resident profile can have its own email credentials.

   **For each resident profile:**
   - Go to Resident Profiles → Edit Profile
   - Enter the resident's email address
   - Enter the email account password (App Password for Gmail)
   - This allows personalized alerts from each resident's email account

   **Supported Email Providers:**
   - Gmail (smtp.gmail.com)
   - Yahoo (smtp.mail.yahoo.com)
   - Outlook/Hotmail (smtp-mail.outlook.com)

   **Gmail Setup:**
   1. Enable 2-Factor Authentication
   2. Generate an App Password: Security → App passwords → Generate
   3. Use the 16-character App Password (not regular password)

6. **Run the Server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the Dashboard:**
   Open your browser and go to `http://127.0.0.1:8000/`
   Login with username: `VIK` and password: `VB1234`

## Project Structure

```
household_electricity_dashboard/
├── dashboard/                  # Main application directory
│   ├── migrations/             # Database migrations
│   ├── static/                 # Static files (CSS, JS)
│   ├── templates/              # HTML templates
│   ├── fixtures/               # Sample data
│   ├── management/commands/    # Custom management commands
│   ├── models.py               # Database models
│   ├── views.py                # View functions
│   ├── forms.py                # Form classes
│   └── urls.py                 # URL patterns
├── household_electricity_dashboard/  # Project settings
├── db.sqlite3                  # SQLite database
├── manage.py                   # Django management script
└── requirements.txt            # Python dependencies
```

## New Features Added

- **Trend Analysis:** Compares energy usage between the last week and the previous week
- **Smart Alerts:** Automatically generates alerts when appliance usage exceeds daily thresholds
- **Professional UI:** Enhanced styling with modern design, responsive layout, and theme toggle
- **Alert Management:** View and mark alerts as read
- **Improved Dashboard:** Shows key metrics, recent alerts, and energy saving tips
- **Default User:** Pre-configured login credentials for easy access
- **Email Alerts:** Automatic high-usage email notifications to resident profiles
- **Manual Alerts:** One-click alert sending from resident profiles
- **Automatic Alert Checking:** Dashboard button to check usage and send alerts instantly

## Alert System Features

### Automatic Email Alerts:
- **Bulk Email System:** Checks all resident profiles and sends alerts to those exceeding thresholds
- **High Usage Detection:** Automatically monitors monthly usage against configurable thresholds (default: 100 kWh)
- **Email Notifications:** Sends detailed usage reports to all affected resident email addresses
- **Database Alerts:** Creates persistent alert records for each resident
- **Detailed Feedback:** Shows which residents received alerts and their usage details

### Manual Alert Sending:
- **Individual Alerts:** Send usage summaries to specific resident profiles
- **One-Click Alerts:** Direct alert sending from resident profile cards
- **Real-time Data:** Includes current month energy consumption and costs
- **Popup Confirmations:** User-friendly confirmation dialogs and success messages

### Usage:
1. **Configure Email Per Profile:** Edit each resident profile to add email credentials
2. **Create Resident Profiles:** Add email addresses and passwords for alert recipients
3. **Bulk Automatic Alerts:** Click "Check All Alerts" on dashboard to monitor all residents
4. **Individual Manual Alerts:** Click "Send Alert" on specific resident profile cards
5. **View Alert History:** Check the Alerts page for complete notification history

## Usage

1. **Login:** Use username "VIK" and password "VB1234"
2. **Add Appliances:** Set up your household appliances with power ratings, thresholds, and critical status
3. **Record Usage:** Log daily usage hours for each appliance
4. **Monitor Trends:** View weekly usage trends on the dashboard
5. **Manage Critical Appliances:** 
   - Go to "Critical Appliances" page
   - Mark appliances requiring digital meters
   - Set monitoring priorities
   - Review AI suggestions for critical appliances
6. **Check Alerts:** Review any high-usage alerts and mark them as read
7. **Export Data:** Download usage reports in CSV or PDF format
│   ├── models.py               # Database models
│   ├── views.py                # View functions
│   ├── urls.py                 # URL routing
│   ├── tests.py                # Test cases
│   └── fixtures/               # Sample data
├── household_electricity_dashboard/
│   ├── settings.py             # Project settings
│   ├── urls.py                 # Project URL routing
│   └── wsgi.py                 # WSGI configuration
├── manage.py                   # Command-line utility
└── requirements.txt            # Project dependencies
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd household_electricity_dashboard
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```
   python manage.py migrate
   ```

5. **Load sample data:**
   ```
   python manage.py loaddata fixtures/appliances.json
   python manage.py loaddata fixtures/usage_records.json
   ```

6. **Run the development server:**
   ```
   python manage.py runserver
   ```

7. **Access the dashboard:**
   Open your web browser and go to `http://127.0.0.1:8000/`.

## License

This project is licensed under the MIT License. See the LICENSE file for details.