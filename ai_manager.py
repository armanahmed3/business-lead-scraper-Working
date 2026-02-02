
import streamlit as st
import requests

# --- UNIFIED AI CLIENT ---
def query_ai_model(prompt, system_role="You are a helpful assistant.", model=None, temperature=0.7):
    """
    Routes the AI request to the configured default provider (AIMLAPI, OpenRouter, Bytez, etc.).
    Uses persistent keys from session state.
    """
    provider = st.session_state.get('default_provider', 'openrouter').lower()
    
    # 1. AIMLAPI Integration - Temporarily Disabled
    if provider == 'aimlapi':
        return {"error": "AIMLAPI temporarily disabled. Please use OpenRouter from Settings which offers free models."}

    # 2. OpenRouter Integration
    elif provider == 'openrouter':
        api_key = st.session_state.get('openrouter_api_key', '')
        if not api_key:
            return {"error": "OpenRouter Key is missing. Please configure it in Settings."}
            
        try:
            # Define priority fallback models focusing on free options
            # List in order of preference, free models first
            fallback_models = [
                "google/gemma-7b-it:free",  # Lightweight, efficient free model
                "mistralai/mistral-7b-instruct:free",  # Popular free model
                "openchat/openchat-7b:free",  # Open-source free model
                "meta-llama/llama-3.1-8b-instruct:free",  # Latest Llama free model
                "nousresearch/hermes-2-pro:free",  # Another good free option
                "microsoft/wizardlm-2-8b:free",  # Free alternative
                "neversleep/noromaid-mixtral:free",  # Free mixtral variant
                "meta-llama/llama-3.1-70b-instruct"  # Non-free fallback
            ]
            
            # Try each model in sequence until one works
            last_error = None
            for or_model in fallback_models:
                try:
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "HTTP-Referer": "http://localhost:8501",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": or_model,
                            "messages": [
                                {"role": "system", "content": system_role},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": temperature
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        return {"content": response.json()['choices'][0]['message']['content']}
                    elif response.status_code == 429:
                        # Rate limit - try next model
                        last_error = f"Rate limit exceeded for model {or_model}: {response.text}"
                        continue
                    elif response.status_code == 402:
                        # Payment required - try next model
                        last_error = f"Payment required for model {or_model}: {response.text}"
                        continue
                    elif response.status_code == 400:
                        # Bad request - might be model-specific issue, try next
                        last_error = f"Bad request for model {or_model}: {response.text}"
                        continue
                    else:
                        # Other error - try next model
                        last_error = f"Model {or_model} error ({response.status_code}): {response.text}"
                        continue
                except Exception as e:
                    last_error = f"Model {or_model} exception: {str(e)}"
                    continue
            
            # If all models failed
            error_msg = f"OpenRouter: All fallback models failed. Last error: {last_error if last_error else 'Unknown error'}"
            return {"error": error_msg}
            
        except Exception as e:
            return {"error": f"OpenRouter Connection Failed: {str(e)}"}

    # 3. Bytez Integration - Temporarily Disabled
    elif provider == 'bytez':
        return {"error": "Bytez temporarily disabled. Please use OpenRouter from Settings which offers free models."}

    else:
        return {"error": f"Unknown Provider: {provider}"}

def global_settings_page(db_handler=None):
    st.markdown("## ⚙️ Global Settings")
    st.markdown("Configure your AI powerhouses and application preferences here. Keys are saved securely for your lifetime access.")
    
    # Use the provided db_handler or fall back to session state db
    db_to_use = db_handler or st.session_state.get('db_handler')
    if not db_to_use:
        st.error("Database handler not available. Settings cannot be saved.")
        return
    
    # Generate a unique key based on the current session to prevent duplicate element key errors
    import time
    unique_key_suffix = str(int(time.time() * 1000) % 1000000)  # Millisecond timestamp modulo 1M for uniqueness
    
    with st.container(border=True):
        st.subheader("🧠 AI Concierge Configuration")
        
        # Provider Selection
        current_provider = st.session_state.get('default_provider', 'openrouter')  # Changed default to openrouter as per user request
        new_provider = st.radio(
            "Select Your Primary AI Network",
            ['openrouter'],  # Only OpenRouter is available now
            index=['openrouter'].index(current_provider) if current_provider in ['openrouter'] else 0,
            horizontal=True,
            format_func=lambda x: x.upper() + " (Recommended - Free)",
            key=f"provider_selection_radio_{unique_key_suffix}"  # Dynamic unique key
        )
        
        if new_provider != current_provider:
            st.session_state.default_provider = new_provider
            db_to_use.update_settings(st.session_state.username, {'default_provider': new_provider})
            st.success(f"Default provider updated to {new_provider.upper()}")
            st.rerun()
        
        # Display current provider status
        st.info(f"🔄 Current AI Provider: **{current_provider.upper()}** (Default selected)")

        st.divider()
        
        # Only show OpenRouter settings
        st.markdown("### 🔓 OpenRouter (Recommended - Free)")
        or_key = st.text_input("OpenRouter Key", value=st.session_state.get('openrouter_api_key', ''), type="password", key=f"set_or_{unique_key_suffix}")
        if st.button("Save OpenRouter Key", key=f"save_or_{unique_key_suffix}"):
            db_to_use.update_settings(st.session_state.username, {'openrouter_key': or_key})
            st.session_state.openrouter_api_key = or_key
            st.success("Saved!")
                
    with st.container(border=True):
        st.subheader("📧 Email Deployment Settings")
        smtp_user = st.text_input("SMTP Username (Gmail)", value=st.session_state.get('smtp_user', ''), key=f"set_smtp_u_{unique_key_suffix}")
        smtp_pass = st.text_input("SMTP Password (App Password)", value=st.session_state.get('smtp_pass', ''), type="password", key=f"set_smtp_p_{unique_key_suffix}")
        if st.button("Save Email Config", key=f"save_email_{unique_key_suffix}"):
            db_to_use.update_settings(st.session_state.username, {'smtp_user': smtp_user, 'smtp_pass': smtp_pass})
            st.session_state.smtp_user = smtp_user
            st.session_state.smtp_pass = smtp_pass
            st.success("Email settings secured.")
