import streamlit as st
import pandas as pd
import json
import tempfile
from datetime import datetime
from pathlib import Path
from realistic_google_maps_scraper import RealisticGoogleMapsScraper, BusinessLead

# Configure page
st.set_page_config(
    page_title="Realistic Business Lead Generator",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Realistic Business Lead Generator")
st.markdown("Generate real, unique business leads with social media links")

# Sidebar
st.sidebar.header("⚙️ Settings")
delay = st.sidebar.slider("Delay between requests (seconds)", 0.5, 5.0, 1.5, 0.1)
max_results = st.sidebar.number_input("Max Results", min_value=1, max_value=50, value=10)

# Main interface
col1, col2 = st.columns(2)

with col1:
    query = st.text_input("Business Type", placeholder="e.g., Dentist, Restaurant, Hotel", 
                         help="What type of businesses are you looking for?")
    
with col2:
    location = st.text_input("Location", placeholder="e.g., Dubai, New York, London", 
                            help="City or region to search in")

# Export format selection
formats = st.multiselect(
    "Export Formats",
    ["CSV", "JSON", "Excel"],
    default=["CSV", "JSON"],
    help="Select the formats you want to export your leads in"
)

# Generate button
if st.button("🚀 Generate Real Leads", type="primary", use_container_width=True):
    if not query or not location:
        st.error("❌ Please enter both business type and location")
    else:
        # Status containers
        status_container = st.empty()
        progress_bar = st.progress(0)
        results_container = st.container()
        
        try:
            # Initialize status
            status_container.info("🔄 Initializing realistic scraper...")
            progress_bar.progress(10)
            
            # Create realistic scraper
            scraper = RealisticGoogleMapsScraper(delay=delay)
            
            status_container.info(f"🔍 Searching for '{query}' in '{location}'...")
            progress_bar.progress(30)
            
            # Perform scraping
            leads = scraper.scrape(query, location, max_results=max_results)
            
            status_container.info("⚙️ Processing and enriching results...")
            progress_bar.progress(70)
            
            # Convert to dictionary format for export
            leads_data = []
            for lead in leads:
                lead_dict = {
                    'name': lead.name,
                    'address': lead.address,
                    'phone': lead.phone,
                    'email': lead.email,
                    'website': lead.website,
                    'category': lead.category,
                    'rating': lead.rating,
                    'reviews': lead.reviews,
                    'latitude': lead.latitude,
                    'longitude': lead.longitude,
                    'maps_url': lead.maps_url,
                    'place_id': lead.place_id,
                    'facebook': lead.facebook,
                    'twitter': lead.twitter,
                    'linkedin': lead.linkedin,
                    'instagram': lead.instagram,
                    'youtube': lead.youtube,
                    'tiktok': lead.tiktok,
                    'timestamp': lead.timestamp,
                    'source_url': lead.source_url
                }
                leads_data.append(lead_dict)
            
            # Export results
            status_container.info("💾 Preparing exports...")
            progress_bar.progress(90)
            
            exported_files = []
            
            if "CSV" in formats:
                df = pd.DataFrame(leads_data)
                csv_file = f"real_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(csv_file, index=False)
                exported_files.append(('CSV', csv_file))
            
            if "JSON" in formats:
                json_file = f"real_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(leads_data, f, indent=2, ensure_ascii=False)
                exported_files.append(('JSON', json_file))
            
            if "Excel" in formats:
                df = pd.DataFrame(leads_data)
                excel_file = f"real_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(excel_file, index=False)
                exported_files.append(('Excel', excel_file))
            
            # Final status
            progress_bar.progress(100)
            status_container.success("✅ Lead generation completed successfully!")
            
            # Display results summary
            with results_container:
                st.subheader("📊 Results Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Leads", len(leads_data))
                
                with col2:
                    social_media_count = sum(1 for lead in leads_data if any([
                        lead['facebook'], lead['twitter'], lead['linkedin'],
                        lead['instagram'], lead['youtube'], lead['tiktok']
                    ]))
                    st.metric("With Social Media", social_media_count)
                
                with col3:
                    contact_count = sum(1 for lead in leads_data if any([
                        lead['phone'], lead['email'], lead['website']
                    ]))
                    st.metric("With Contact Info", contact_count)
                
                with col4:
                    unique_locations = len(set(lead['address'] for lead in leads_data if lead['address']))
                    st.metric("Unique Locations", unique_locations)
                
                # Show sample results
                if leads_data:
                    st.subheader("📋 Sample Results")
                    
                    # Display first 5 results in a table
                    sample_df = pd.DataFrame(leads_data[:min(5, len(leads_data))])
                    display_columns = ['name', 'address', 'phone', 'email', 'website']
                    st.dataframe(sample_df[display_columns].fillna('N/A'))
                    
                    # Show social media distribution
                    st.subheader("🌍 Social Media Distribution")
                    social_stats = {
                        'Facebook': sum(1 for lead in leads_data if lead['facebook']),
                        'Twitter': sum(1 for lead in leads_data if lead['twitter']),
                        'LinkedIn': sum(1 for lead in leads_data if lead['linkedin']),
                        'Instagram': sum(1 for lead in leads_data if lead['instagram']),
                        'YouTube': sum(1 for lead in leads_data if lead['youtube']),
                        'TikTok': sum(1 for lead in leads_data if lead['tiktok'])
                    }
                    
                    social_df = pd.DataFrame(list(social_stats.items()), 
                                           columns=['Platform', 'Count'])
                    st.bar_chart(social_df.set_index('Platform'))
                
                # Export download buttons
                st.subheader("📥 Download Results")
                cols = st.columns(len(exported_files))
                
                for i, (format_name, file_path) in enumerate(exported_files):
                    with cols[i]:
                        with open(file_path, 'rb') as f:
                            st.download_button(
                                label=f"📥 Download {format_name}",
                                data=f.read(),
                                file_name=file_path,
                                mime=f"text/{format_name.lower()}" if format_name != 'Excel' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                
                # Show detailed results
                st.subheader("📋 Detailed Results")
                detailed_df = pd.DataFrame(leads_data)
                st.dataframe(detailed_df.fillna('N/A'))
                
        except Exception as e:
            status_container.error(f"❌ Error occurred: {str(e)}")
            progress_bar.progress(0)
            st.error("Failed to generate leads. Please try again.")

# Information section
st.markdown("---")
st.info("""
🔍 **How it works:**
- Searches for real businesses using multiple legitimate approaches
- Extracts detailed information including contact details
- Visits business websites to extract social media links
- Ensures all leads are real and unique through advanced deduplication
- Never shows demo or sample data - only real business information

🛡️ **Features:**
- Realistic scraping that mimics human behavior
- Proper rate limiting and delays
- Advanced social media extraction
- 100% unique lead guarantee
- Multiple export formats
""")

# Footer
st.markdown("---")
st.caption("Realistic Business Lead Generator - Real Data Only • No Demo Content • Maximum Uniqueness")