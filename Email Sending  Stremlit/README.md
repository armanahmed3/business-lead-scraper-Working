---
title: LeadAI Pro
emoji: 🚀
colorFrom: indigo
colorTo: purple
sdk: streamlit
app_file: deploy_app.py
python_version: 3.10
---
# 🚀 LeadAI Pro - AI-Powered Lead Management & Email Marketing Platform

LeadAI Pro is a comprehensive AI-powered platform for lead management and email marketing, designed for deployment on Hugging Face Spaces. It provides a complete solution for managing leads, creating targeted email campaigns, and tracking performance with advanced analytics.

## ✨ Features

### 🎯 Core Features
- **📁 CSV Upload & Data Processing** - Upload client data with automatic validation and processing
- **🤖 AI-Powered Email Generation** - Generate personalized emails using free Hugging Face models
- **📊 Advanced Analytics & Tracking** - Real-time performance metrics and engagement tracking
- **⏰ Scheduled Email Campaigns** - Schedule emails for optimal delivery times
- **👥 Lead Management & Scoring** - Organize and score leads with categories
- **🎯 Role-Based Access Control** - Admin and User roles with different permissions

### 🆕 What's New (v2.0)
- **📧 Multi-Profile Email System** - Configure multiple SMTP profiles with OAuth2 support
- **⚡ Real-time Counters** - Live metrics updates using WebSocket technology
- **📎 Email Attachments** - Send files with your email campaigns
- **🚫 Suppression Lists** - Manage blocked email addresses and domains
- **🔄 Retry & Recovery** - Automatic retry with exponential backoff for failed sends
- **📊 Advanced Campaign Controls** - Dry-run mode, send windows, rate limiting, and warmup
- **🎯 Smart Targeting** - Preview recipients, deduplication, and safety thresholds
- **📈 UTM Tracking** - Automatic UTM parameter injection for link tracking
- **⚙️ Custom Headers** - Add custom email headers for advanced deliverability

### 🔧 Technical Features
- **User Authentication** - Secure login/signup with hashed passwords
- **SQLite Database** - Persistent data storage for leads, campaigns, and tracking
- **Email Tracking** - Track opens, clicks, and engagement metrics
- **AI Assistant** - Free Hugging Face models for content generation and improvement
- **Export Functionality** - Export campaign logs and lead data as CSV
- **3D Animated UI** - Modern, professional interface with smooth transitions

## 🚀 Quick Start

### Local Development
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python start_local.py
   ```
   Or directly:
   ```bash
   streamlit run deploy_app.py
   ```

### Hugging Face Spaces Deployment
1. Create a new Space on Hugging Face
2. Upload all files to your Space
3. Set the Space SDK to Streamlit
4. The app will automatically deploy!

### Sample Data
Use `sample_leads.csv` to test the application with pre-loaded lead data.

## 📋 File Structure

```
LeadAI Pro/
├── deploy_app.py          # Main Streamlit application
├── requirements.txt       # Python dependencies
├── runtime.txt           # Hugging Face Spaces runtime
├── README.md             # This file
└── leadai_pro.db         # SQLite database (created automatically)
```

## 🎯 Usage Guide

### 1. Authentication
- **Sign Up**: Create a new account with username, email, and password
- **Login**: Access your account with secure authentication
- **Roles**: Admin and User roles with different access levels

### 2. Lead Management
- **Upload CSV**: Upload client data with columns: name, email, company, phone, title, industry
- **Categorize**: Assign categories to organize leads (e.g., "Graphic Design Clients")
- **View & Filter**: Browse leads with category and status filters
- **Export**: Download lead data as CSV

### 3. Email Campaigns
- **Create Campaign**: Set campaign name, subject, and email body
- **AI Generation**: Use AI to generate subject lines and improve content
- **Targeting**: Select leads by category or send to all
- **Scheduling**: Send immediately or schedule for later
- **Tracking**: Monitor delivery, opens, and clicks
- **Multi-Profile Support**: Choose from multiple configured email profiles
- **Advanced Controls**: Rate limiting, send windows, dry-run mode, and warmup
- **Attachments**: Upload and send files with your campaigns
- **Preview & Safety**: Preview recipients before sending with safety thresholds

### 4. AI Assistant
- **Email Generation**: Generate personalized emails for specific leads
- **Content Improvement**: Enhance existing email content
- **Subject Lines**: AI-powered subject line suggestions
- **Free Models**: Uses free Hugging Face models (no API costs)

### 5. Dashboard & Analytics
- **Real-time Metrics**: View lead counts, email performance, and engagement rates
- **Visual Charts**: Interactive charts for lead distribution and email performance
- **Campaign History**: Track all campaigns and their results
- **Export Reports**: Download campaign logs and analytics
- **Live Counters**: WebSocket-powered real-time updates on every page
- **Advanced Tracking**: UTM parameters, custom headers, and detailed engagement metrics

## 🔧 Configuration

### Environment Variables
The app works out of the box with default settings. For production use, you can configure:

- **SMTP Settings**: For actual email sending (currently simulated)
- **Database**: SQLite database (automatically created)
- **AI Models**: Free Hugging Face models (automatically loaded)
- **WebSocket URL**: For real-time metrics (default: ws://localhost:8000/ws/metrics)
- **Multiple Email Profiles**: Configure via UI - no environment variables needed

### Database Schema
- **Users**: Authentication and role management
- **Leads**: Client information and categorization
- **Campaigns**: Email campaign details and scheduling
- **Email Tracking**: Delivery and engagement tracking

## 🎨 UI/UX Features

### Modern Design
- **3D Animated Interface** - Smooth transitions and hover effects
- **Professional Styling** - Clean, modern design with gradient backgrounds
- **Responsive Layout** - Works on desktop and mobile devices
- **Interactive Elements** - Engaging buttons and animations

### User Experience
- **Intuitive Navigation** - Easy-to-use tabbed interface
- **Real-time Feedback** - Progress bars and status updates
- **Error Handling** - Graceful error handling with helpful messages
- **Data Validation** - Input validation and CSV processing

## 🔒 Security Features

- **Password Hashing** - Secure password storage with SHA-256
- **Input Validation** - Email validation and data sanitization
- **SQL Injection Protection** - Parameterized queries
- **Session Management** - Secure user sessions

## 📊 Analytics & Tracking

### Email Metrics
- **Delivery Rate** - Percentage of successfully sent emails
- **Open Rate** - Percentage of emails opened by recipients
- **Click Rate** - Percentage of emails with link clicks
- **Engagement Tracking** - Real-time engagement monitoring

### Lead Analytics
- **Lead Scoring** - Automatic lead scoring (20-95 points)
- **Category Distribution** - Lead distribution by category
- **Status Tracking** - Lead status and progression
- **Performance Metrics** - Campaign performance analysis

## 🤖 AI Features

### Free AI Models
- **Text Generation** - GPT-2 model for content generation
- **Subject Line Generation** - AI-powered subject line suggestions
- **Content Improvement** - Enhance existing email content
- **No API Costs** - Uses free Hugging Face models

### AI Capabilities
- **Personalization** - Generate personalized content for each lead
- **Campaign Optimization** - Suggest improvements for better engagement
- **Content Enhancement** - Improve email readability and effectiveness
- **Smart Suggestions** - AI-powered recommendations

## 🚀 Deployment

### Hugging Face Spaces
1. **Create Space**: Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. **Upload Files**: Upload all project files
3. **Set SDK**: Choose Streamlit as the SDK
4. **Deploy**: The app will automatically deploy and be available

### Requirements
- **Python 3.8+** - Compatible with Hugging Face Spaces
- **Streamlit** - Web framework for the application
- **Free Resources** - Uses only free Hugging Face models and services

## 🔧 Troubleshooting

### Common Issues
1. **CSV Upload Errors**: Ensure CSV has required columns (name, email, company)
2. **Email Sending**: Currently simulated - configure SMTP for real sending
3. **AI Model Loading**: Models load automatically on first use
4. **Database Issues**: SQLite database is created automatically

### Support
- **Error Messages**: Clear error messages with solutions
- **Validation**: Input validation prevents common errors
- **Logging**: Detailed logging for debugging
- **Fallbacks**: Graceful fallbacks for AI model failures

## 📈 Performance

### Optimization
- **Efficient Database Queries** - Optimized SQL queries
- **Lazy Loading** - AI models loaded only when needed
- **Caching** - Session state management for better performance
- **Async Operations** - Non-blocking email sending

### Scalability
- **SQLite Database** - Handles thousands of leads efficiently
- **Batch Processing** - Efficient bulk email sending
- **Memory Management** - Optimized memory usage
- **Error Recovery** - Robust error handling and recovery

## 🎯 Use Cases

### Small Businesses
- **Lead Management** - Organize and track potential customers
- **Email Marketing** - Send targeted campaigns to leads
- **Performance Tracking** - Monitor campaign effectiveness
- **AI Assistance** - Generate professional email content

### Marketing Agencies
- **Client Management** - Manage multiple client campaigns
- **Campaign Automation** - Schedule and automate email campaigns
- **Analytics & Reporting** - Detailed performance analytics
- **Content Generation** - AI-powered content creation

### Freelancers
- **Lead Organization** - Categorize and score leads
- **Professional Emails** - Generate polished email content
- **Campaign Tracking** - Monitor email performance
- **Time Saving** - Automate repetitive tasks

## 🔮 Future Enhancements

### Planned Features
- **Advanced AI Models** - Integration with more AI models
- **Email Templates** - Pre-built email templates
- **A/B Testing** - Test different email versions
- **Integration APIs** - Connect with external services
- **Mobile App** - Native mobile application
- **Advanced Analytics** - More detailed reporting
- **Email Automation** - Drip campaigns and follow-up sequences
- **Advanced Segmentation** - Dynamic lead segmentation rules

### Technical Improvements
- **Real Email Sending** - ✅ SMTP integration for actual email delivery (v2.0)
- **Advanced Security** - Enhanced security features
- **Performance Optimization** - Further performance improvements
- **Database Migration** - Support for different databases
- **API Development** - REST API for external integrations
- **Real-time Updates** - ✅ WebSocket-powered live metrics (v2.0)

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For support, please open an issue on the GitHub repository or contact the development team.

---

**LeadAI Pro** - Empowering businesses with AI-driven lead management and email marketing solutions. 🚀