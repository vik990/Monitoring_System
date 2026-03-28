# Appliance Detection and Identification Guide

## Overview

Your Django dashboard now has advanced appliance detection capabilities! The system can automatically identify what appliance is plugged into your Tuya smart plug based on power consumption patterns, and you can also manually identify appliances for better accuracy.

## What's New ✨

### **Automatic Appliance Detection**
Your dashboard can now automatically detect and identify appliances based on their power consumption patterns:

- **Smart Pattern Recognition**: Analyzes power usage to identify common household appliances
- **Real-time Detection**: Updates appliance identification in real-time
- **Confidence Scoring**: Provides confidence levels for each detection
- **Usage History Analysis**: Learns from historical usage patterns

### **Manual Appliance Identification**
You can manually identify appliances for better accuracy:

- **Comprehensive Appliance Library**: 17 different appliance types to choose from
- **Custom Naming**: Add your own names for identified appliances
- **One-Click Identification**: Simple interface for manual identification

## Detected Appliance Types 🔌

The system can automatically detect these appliance types:

### **Kitchen Appliances**
- 🧊 **Refrigerator/Freezer** (100-200W) - Cyclic operation
- 🍿 **Microwave Oven** (600-1500W) - Short bursts
- ☕ **Electric Kettle** (1500-3000W) - Short bursts
- 🍞 **Toaster** (800-1800W) - Short bursts
- ☕ **Coffee Maker** (800-1500W) - Short cycles

### **Climate Control**
- ❄️ **Air Conditioner** (1000-3500W) - Cyclic operation
- 🌪️ **Electric Fan** (20-100W) - Continuous operation

### **Laundry**
- 👕 **Washing Machine** (400-2500W) - Intermittent operation
- 👗 **Clothes Dryer** (1800-5000W) - Continuous during cycle
- 🔥 **Clothes Iron** (800-1800W) - Intermittent operation

### **Electronics & Entertainment**
- 💻 **Computer/Laptop** (50-500W) - Variable usage
- 📺 **Television** (50-400W) - Continuous during use
- 🎮 **Gaming Console** (50-350W) - Variable usage

### **Personal Care**
- 💨 **Hair Dryer** (800-1800W) - Short bursts

### **Other**
- 🧹 **Vacuum Cleaner** (500-3000W) - Short bursts
- 💡 **LED/Lighting** (5-100W) - Continuous during use

## How It Works 🧠

### **Automatic Detection Process**

1. **Real-time Monitoring**: System continuously monitors power consumption
2. **Pattern Analysis**: Compares current power usage with known appliance patterns
3. **Confidence Scoring**: Assigns confidence levels based on match quality
4. **Historical Learning**: Improves accuracy over time with usage history

### **Detection Confidence Levels**

- **HIGH** (90-100%): Exact match with known power range
- **MEDIUM** (60-89%): Close match, may need verification
- **LOW** (30-59%): Distant match, manual identification recommended
- **UNKNOWN** (0%): No match found, manual identification required

## Using the Appliance Detection System 🚀

### **Accessing the Detection Interface**

1. **Via URL**: Visit `http://127.0.0.1:8000/appliance-detection/`
2. **Via Navigation**: Add a link to your dashboard navigation

### **Viewing Current Detection**

The detection interface shows:

- **Current Appliance**: Automatically detected appliance with confidence level
- **Live Metrics**: Real-time power, current, and voltage readings
- **Usage History**: 7-day usage statistics and patterns
- **Recommendations**: Energy-saving tips based on current usage

### **Manual Identification**

If automatic detection is incorrect:

1. **Navigate to Detection Page**: Go to the appliance detection interface
2. **Select Appliance Type**: Choose from the dropdown list
3. **Add Custom Name** (Optional): Enter a custom name for the appliance
4. **Click Identify**: Confirm the identification

## Dashboard Integration 📊

### **Enhanced Dashboard Display**

The main dashboard now shows:

- **Live Appliance Information**: Current appliance being monitored
- **Real-time Power Data**: Live power consumption metrics
- **Energy Cost Calculations**: Real-time cost based on current usage
- **Appliance Status**: Whether the appliance is currently on/off

### **API Endpoints**

Available API endpoints for appliance detection:

- `GET /appliance-info/` - Get current appliance information
- `POST /identify-appliance/` - Manually identify an appliance
- `GET /appliance-detection/` - View detection interface

## Benefits of Appliance Detection 🎯

### **For Users**

1. **Automatic Identification**: No need to manually track what's plugged in
2. **Energy Insights**: Understand which appliances consume the most energy
3. **Usage Patterns**: Learn when and how long appliances are used
4. **Cost Tracking**: See energy costs broken down by appliance type

### **For Energy Management**

1. **Peak Usage Identification**: Find out which appliances cause peak demand
2. **Usage Optimization**: Identify opportunities to reduce energy consumption
3. **Appliance Efficiency**: Monitor how efficiently appliances are operating
4. **Maintenance Alerts**: Detect when appliances may need servicing

## Technical Implementation 🔧

### **Detection Algorithm**

The detection system uses:

- **Power Range Matching**: Compares current power with known appliance ranges
- **Pattern Recognition**: Analyzes usage patterns over time
- **Confidence Scoring**: Mathematical scoring for detection accuracy
- **Historical Analysis**: Learns from past usage data

### **Data Storage**

Detected appliances are stored as:

- **Separate Appliance Records**: Each identified appliance gets its own record
- **Usage History**: Detailed usage tracking for each appliance
- **MySQL Integration**: Data stored in both SQLite and MySQL databases
- **Real-time Updates**: Live data updates every minute

## Troubleshooting 🔍

### **Common Issues**

#### **1. Low Detection Confidence**
- **Cause**: Power consumption doesn't match known patterns
- **Solution**: Manually identify the appliance or check if appliance is operating normally

#### **2. Wrong Appliance Detection**
- **Cause**: Similar power consumption between different appliances
- **Solution**: Use manual identification to correct the appliance type

#### **3. No Detection**
- **Cause**: No power consumption or unknown appliance type
- **Solution**: Check if appliance is plugged in and turned on, then manually identify

#### **4. Inconsistent Detection**
- **Cause**: Variable power consumption (e.g., appliances with variable speed)
- **Solution**: Manual identification may be more reliable for such appliances

### **Improving Detection Accuracy**

1. **Ensure Stable Power Supply**: Fluctuations can affect detection
2. **Use During Normal Operation**: Detect when appliance is operating normally
3. **Manual Verification**: Verify automatic detections manually
4. **Regular Updates**: Keep appliance library updated with new appliance types

## Future Enhancements 🔮

### **Planned Features**

1. **Machine Learning**: AI-powered detection for better accuracy
2. **Voice Integration**: Voice commands for appliance identification
3. **Mobile App**: Mobile interface for on-the-go monitoring
4. **Smart Home Integration**: Integration with other smart home devices
5. **Predictive Maintenance**: Alerts for potential appliance issues

### **Custom Appliance Types**

You can easily add new appliance types by:

1. **Editing the Pattern Library**: Add new entries to `APPLIANCE_PATTERNS`
2. **Defining Power Ranges**: Specify typical power consumption ranges
3. **Adding Descriptions**: Include detailed descriptions and categories
4. **Testing Detection**: Verify detection works correctly

## Usage Examples 📱

### **Example 1: Refrigerator Detection**
```
Current Detection: 🧊 Refrigerator/Freezer
Confidence: HIGH (100%)
Power: 150W
Pattern: Cyclic (on/off every 10-30 mins)
```

### **Example 2: Microwave Detection**
```
Current Detection: 🍿 Microwave Oven
Confidence: HIGH (100%)
Power: 1200W
Pattern: Short bursts (1-10 minutes)
```

### **Example 3: Manual Identification**
```
User Action: Select "Washing Machine" from dropdown
Custom Name: "My Front-Load Washer"
Result: Appliance identified as "My Front-Load Washer"
```

## Integration with Existing Features 🔗

### **Resident Profiles**
- Each identified appliance is associated with a resident profile
- Usage data is tracked per resident for personalized insights

### **Alerts and Notifications**
- High usage alerts can be appliance-specific
- Energy-saving recommendations are tailored to detected appliances

### **Charts and Analytics**
- Usage charts can be filtered by appliance type
- Energy consumption analysis by appliance category

### **Export Features**
- Usage data can be exported with appliance identification
- Detailed reports include appliance-specific information

## Conclusion 🎉

Your dashboard now provides intelligent appliance detection that makes energy monitoring much more meaningful. You can:

- **Automatically identify** what's plugged into your smart plug
- **Track energy usage** by specific appliance types
- **Get personalized recommendations** based on detected appliances
- **Monitor usage patterns** over time for better energy management

The system combines automatic detection with manual identification options, giving you both convenience and accuracy in tracking your household energy consumption!

## Support 🆘

If you need help with appliance detection:

1. **Check the Detection Interface**: Visit `/appliance-detection/` for real-time information
2. **Manual Identification**: Use the manual identification feature for better accuracy
3. **Review Usage Patterns**: Check historical data for insights
4. **Contact Support**: If issues persist, provide details about your appliance and usage patterns