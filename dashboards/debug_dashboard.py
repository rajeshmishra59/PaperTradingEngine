import streamlit as st
import subprocess
import psutil
import pytz
from datetime import datetime

st.title("🔍 Debug Dashboard - Bot Status")

def get_simple_bot_status():
    try:
        # Method 1: pgrep
        result1 = subprocess.run(['pgrep', '-f', 'main_papertrader'], 
                              capture_output=True, text=True)
        method1_result = len(result1.stdout.strip()) > 0
        
        # Method 2: ps aux
        ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        method2_result = 'main_papertrader' in ps_result.stdout
        
        # Final decision
        bot_running = method1_result or method2_result
        
        return {
            'method1_pgrep': method1_result,
            'method2_ps': method2_result,
            'final_decision': bot_running,
            'pgrep_output': repr(result1.stdout),
            'error': None
        }
    except Exception as e:
        return {
            'method1_pgrep': False,
            'method2_ps': False,
            'final_decision': False,
            'pgrep_output': '',
            'error': str(e)
        }

# Get status
status = get_simple_bot_status()

st.write("## Debug Results:")
st.write(f"**Method 1 (pgrep):** {status['method1_pgrep']}")
st.write(f"**Method 2 (ps aux):** {status['method2_ps']}")
st.write(f"**Final Decision:** {status['final_decision']}")
st.write(f"**Pgrep Output:** {status['pgrep_output']}")

if status['error']:
    st.error(f"Error: {status['error']}")

# Show status
if status['final_decision']:
    st.success("🟢 BOT IS RUNNING!")
else:
    st.error("🔴 BOT IS OFFLINE!")

# Market status
ist = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(ist)
market_open = (9, 15) <= (now_ist.hour, now_ist.minute) <= (15, 30)
is_weekday = now_ist.weekday() < 5

st.write(f"**Current Time:** {now_ist.strftime('%H:%M:%S IST')}")
st.write(f"**Market Open:** {market_open and is_weekday}")

# Auto refresh
if st.button("🔄 Refresh"):
    st.rerun()
