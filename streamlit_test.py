import streamlit as st
import subprocess
import time
import threading
from queue import Queue
import sys
import os
from datetime import datetime

def stream_output(process, queue):
    for line in iter(process.stdout.readline, ''):
        queue.put((datetime.now().strftime("%H:%M:%S"), line.strip()))
    process.stdout.close()

def init_session_state():
    if 'control_plane_process' not in st.session_state:
        st.session_state.control_plane_process = None
    if 'output_queue' not in st.session_state:
        st.session_state.output_queue = Queue()
    if 'terminal_output' not in st.session_state:
        st.session_state.terminal_output = []
    if 'auto_scroll' not in st.session_state:
        st.session_state.auto_scroll = True

def get_terminal_style():
    return """
        <style>
        .terminal-container {
            margin: -1rem;
            padding: 1rem;
            background-color: #1e1e1e;
        }
        .terminal {
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            font-family: 'Ubuntu Mono', 'JetBrains Mono', 'Courier New', monospace;
            height: 75vh;
            overflow-y: auto;
            border-radius: 10px;
            border: 1px solid #3d3d3d;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .terminal .error { color: #ff6b6b; }
        .terminal .success { color: #69db7c; }
        .terminal .warning { color: #ffd43b; }
        .terminal .info { color: #4dabf7; }
        .terminal .command { color: #da77f2; }
        .terminal::-webkit-scrollbar {
            width: 12px;
            background-color: #1e1e1e;
        }
        .terminal::-webkit-scrollbar-thumb {
            background-color: #2d2d2d;
            border-radius: 6px;
            border: 2px solid #1e1e1e;
        }
        .status-bar {
            background-color: #2d2d2d;
            color: #d4d4d4;
            padding: 10px 20px;
            border-radius: 5px;
            margin-bottom: 10px;
            font-family: 'Ubuntu Mono', monospace;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #3d3d3d;
        }
        .timestamp {
            color: #888888;
            margin-right: 10px;
            opacity: 0.8;
        }
        .stApp {
            background-color: #1e1e1e;
        }
        .main {
            background-color: #1e1e1e;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background-color: #1e1e1e;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: #2d2d2d;
            border-radius: 5px 5px 0 0;
            gap: 2px;
            color: #d4d4d4;
        }
        .stTabs [aria-selected="true"] {
            background-color: #3d3d3d;
        }
        </style>
    """

def main():
    st.set_page_config(layout="wide")
    
    # Initialize session state
    init_session_state()
    
    # Apply static styling
    st.markdown(get_terminal_style(), unsafe_allow_html=True)
    
    st.title("🎬 Hitchcock AI Film Production Suite")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("System Control")
        
        # Start/Stop System buttons
        if not st.session_state.control_plane_process:
            if st.button("🚀 Start System", key="start_btn", use_container_width=True):
                try:
                    process = subprocess.Popen(
                        ['python', 'control_plane.py'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        bufsize=1,
                        universal_newlines=True
                    )
                    st.session_state.control_plane_process = process
                    st.session_state.terminal_output.append((datetime.now().strftime("%H:%M:%S"), "🚀 Starting Control Plane..."))
                    
                    thread = threading.Thread(
                        target=stream_output,
                        args=(process, st.session_state.output_queue)
                    )
                    thread.daemon = True
                    thread.start()
                    
                    st.success("✅ Control plane started successfully!")
                except Exception as e:
                    st.error(f"❌ Error starting control plane: {e}")
        else:
            if st.button("🛑 Stop System", key="stop_btn", use_container_width=True):
                if st.session_state.control_plane_process:
                    st.session_state.control_plane_process.terminate()
                    st.session_state.control_plane_process = None
                    st.session_state.terminal_output.append((datetime.now().strftime("%H:%M:%S"), "🛑 Control Plane stopped."))
                    st.success("System stopped successfully!")

        st.markdown("---")
        st.subheader("Terminal Controls")
        if st.button("🧹 Clear Terminal", key="clear_btn", use_container_width=True):
            st.session_state.terminal_output = []
        
        st.session_state.auto_scroll = st.checkbox("Auto-scroll", value=st.session_state.auto_scroll)
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["🖥️ Control Plane Terminal", "🤖 Agent Chat"])
    
    with tab1:
        # Status bar with system info
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            status = "🟢 Running" if st.session_state.control_plane_process else "⚫ Stopped"
            st.markdown(f'<div class="status-bar">Status: {status} | Buffer: {len(st.session_state.terminal_output)} lines</div>', unsafe_allow_html=True)
        
        # Terminal output
        terminal = st.empty()
        
        # Update terminal output
        if st.session_state.control_plane_process and st.session_state.control_plane_process.poll() is None:
            try:
                while not st.session_state.output_queue.empty():
                    timestamp, output = st.session_state.output_queue.get_nowait()
                    if output:  # Only append non-empty lines
                        st.session_state.terminal_output.append((timestamp, output))
                        # Keep buffer size manageable
                        if len(st.session_state.terminal_output) > 1000:
                            st.session_state.terminal_output = st.session_state.terminal_output[-1000:]
            except Exception:
                pass
        
        # Display terminal content with timestamps
        terminal_content = "\n".join([f'<span class="timestamp">[{ts}]</span> {out}' for ts, out in st.session_state.terminal_output])
        scroll_js = """
        <script>
            const terminal = document.querySelector('.terminal');
            terminal.scrollTop = terminal.scrollHeight;
        </script>
        """ if st.session_state.auto_scroll else ""
        
        terminal.markdown(
            f'<div class="terminal-container"><div class="terminal">{terminal_content}</div></div>{scroll_js}',
            unsafe_allow_html=True
        )
        
    with tab2:
        # Agent chat styling
        st.markdown("""
        <style>
        .chat-container {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #3d3d3d;
            margin-top: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Agent selection
        agents = ["StoryWriterAgent", "StoryBoarderAgent", "DOPAgent", "AudioAgent"]
        selected_agent = st.selectbox("Select Agent to Chat With", agents)
        
        # Chat interface
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.subheader(f"Chat with {selected_agent}")
        user_input = st.text_input("Your message:", key="agent_input")
        
        if st.button("Send", key="send_button"):
            if st.session_state.control_plane_process:
                try:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    st.session_state.terminal_output.append((timestamp, f"🤖 Connecting to {selected_agent}..."))
                    
                    cmd = f"mahilo connect --agent-name {selected_agent}"
                    process = subprocess.Popen(
                        cmd.split(),
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    output, error = process.communicate(input=user_input)
                    
                    if error:
                        st.error(f"Error: {error}")
                        st.session_state.terminal_output.append((timestamp, f"❌ Error with {selected_agent}: {error}"))
                    else:
                        st.write("🤖 Agent Response:")
                        st.markdown(f"```\n{output}\n```")
                        st.session_state.terminal_output.append((timestamp, f"✅ {selected_agent} responded successfully"))
                except Exception as e:
                    st.error(f"Error communicating with agent: {e}")
                    st.session_state.terminal_output.append((timestamp, f"❌ Communication error with {selected_agent}: {str(e)}"))
            else:
                st.warning("⚠️ Please start the system first!")
        st.markdown('</div>', unsafe_allow_html=True)

    # Auto-refresh for terminal updates
    time.sleep(0.1)
    st.rerun()

if __name__ == "__main__":
    main()