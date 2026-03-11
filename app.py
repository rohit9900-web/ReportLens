import streamlit as st
import pandas as pd
import time
import subprocess
import sys
import os
import sqlite3
import datetime
import db_manager
from db_manager import (
    get_all_patients, update_patient_metadata, get_patient_report, 
    delete_patient_completely, update_test_record, 
    add_manual_test_record, delete_test_record
)

import db_schema
# (If your db_schema.py has a specific function to build tables, call it too. 
# Like: db_schema.create_tables() or whatever you named it).

# --- TOP OF FILE: INITIALIZE SESSION STATE ---
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

import socket

def is_connected():
    try:
        # Pings Google's DNS to check for active internet
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="ReportLens Pro", page_icon="🩺", layout="wide")

# # --- 🎨 PRO MEDICAL DESIGN SYSTEM ---
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;800&display=swap');
    
#     /* 1. GLOBAL SETTINGS */
#     html, body {
#         font-family: 'Manrope', sans-serif;
# /*        color: #0f172a;  */
#         font-size: 16px; 
#     }

#     /* 2. SIDEBAR */
#     section[data-testid="stSidebar"] {
#         background-color: #1e293b;
#         border-right: 1px solid #334155;
#     }
#     section[data-testid="stSidebar"] h1, span, p, label {
#        /* color: #f8fafc !important; */
#     }

#     /* 3. DASHBOARD CARDS (Fancy Style) */
#     .stat-card {
#         background: white;
#         padding: 25px;
#         border-radius: 16px;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#         border: 1px solid #e2e8f0;
#         transition: all 0.3s ease;
#     }
#     .stat-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
#     .stat-val { font-size: 40px; font-weight: 800; /*color: #0f172a; */}
#     .stat-label { font-size: 16px; color: #64748b; font-weight: 600; text-transform: uppercase; }

#     /* 4. CLINICAL REPORTS (FORMAL TABLE DESIGN) */
#     .report-table-header {
#         display: grid;
#         grid-template-columns: 4fr 1.5fr 1.5fr 2fr 1.5fr; /* Columns */
#         background-color: #f1f5f9;
#         padding: 12px 15px;
#         border-bottom: 2px solid #334155;
#         margin-top: 15px;
#     }
#     .header-item {
#         font-size: 14px;
#         font-weight: 800;
#        /* color: #334155; */
#         text-transform: uppercase;
#         letter-spacing: 0.5px;
#     }

#     .report-table-row {
#         display: grid;
#         grid-template-columns: 4fr 1.5fr 1.5fr 2fr 1.5fr; /* Match Header */
#         padding: 12px 15px;
#         border-bottom: 1px solid #e2e8f0;
#         align-items: center;
#         background: white;
#         transition: background 0.1s;
#     }
#     .report-table-row:hover {
#         background-color: #f8fafc;
#     }
    
#     /* Formal Text Styles */
#     .tbl-name { font-weight: 700; color: #0f172a; font-size: 16px; }
#     .tbl-val { font-weight: 700; color: #000000; font-size: 16px; }
#     .tbl-unit { font-size: 14px; color: #64748b; }
#     .tbl-range { font-size: 14px; color: #64748b; }
    
#     /* Formal Status Text (No Badges) */
#     .stat-txt-High { color: #dc2626; font-weight: 700; }
#     .stat-txt-Low { color: #d97706; font-weight: 700; }
#     .stat-txt-Normal { color: #15803d; font-weight: 600; }

#     /* Category Separator */
#     .category-header {
#         background-color: #e2e8f0;
#         padding: 8px 15px;
#         font-weight: 800;
#         font-size: 14px;
#        /* color: #475569; */
#         border-bottom: 1px solid #cbd5e1;
#         margin-top: 0px;
#     }

#     /* 5. BUTTONS (FIXED VISIBILITY FOR BOTH REGULAR AND FORM BUTTONS) */
#     div[data-testid="stButton"] button,
#     div[data-testid="stFormSubmitButton"] button {
#         background: #2563eb !important; /* Bright Blue */
#         /*color: white !important; */        /* White Text */
#         border: none !important;
#         padding: 0.6rem 1.2rem !important;
#         border-radius: 8px !important;
#         font-weight: 700 !important;
#         width: 100% !important;
#         font-size: 16px !important;
#     }
#     div[data-testid="stButton"] button p,
#     div[data-testid="stFormSubmitButton"] button p {
#         color: white !important;
#     }
#     div[data-testid="stButton"] button:hover,
#     div[data-testid="stFormSubmitButton"] button:hover {
#         background: #1e40af !important;
#     }

#     /* 6. INFO BOX & ALERTS (FIXED READABILITY) */
#     .info-box-contrast {
#         background-color: white;
#         border: 2px solid #3b82f6; 
#         padding: 20px;
#         border-radius: 10px;
#         /*color: #0f172a;*/
#     }
#     .info-box-contrast h5 { color: #1e40af !important; font-weight: 800; font-size: 20px; }
#     .info-box-contrast p { color: #334155 !important; font-size: 18px; }

#     /* Force Error/Warning Text to be Black */
#     div[data-testid="stAlert"] { color: #000000 !important; }
#     div[data-testid="stAlert"] p { color: #000000 !important; font-weight: 600 !important; }

#     /* ============================================================ */
#     /* 👇 NEW FIXES: Force specific missing elements to be DARK 👇 */
#     /* ============================================================ */

#     /* 1. Make TAB Text (Edit, Add, Delete) Dark */
#     button[data-baseweb="tab"] div p {
#        /* color: #0f172a !important;*/ 
#         font-weight: 800 !important;
#     }
    
#     /* 2. FORCE ALL INPUT LABELS TO BE DARK (Name, Age, Val, Unit, Range) */
#     label, label *, div[data-testid="stWidgetLabel"] p {
#         /*color: #0f172a !important; */
#         font-weight: 800 !important;
#     }

#     /* 3. Make PATIENT HEADER Text (Age, Gender) Dark */
#     .patient-header-text {
#         /*color: #000000 !important;*/
#         font-weight: 700;
#     }
            

#     /* 4. FORCE SIDEBAR MENU TEXT BACK TO WHITE */
#     section[data-testid="stSidebar"] label,
#     section[data-testid="stSidebar"] label *,
#     section[data-testid="stSidebar"] p,
#     section[data-testid="stSidebar"] span {
#         /*color: #ffffff !important;*/
#         font-weight: 600 !important;
#     }
            

#     /* ========================================== */
#     /* 👇 FINAL FIXES FOR EXPANDER & SIDEBAR 👇   */
#     /* ========================================== */

#     /* 1. Force the Expander Title ("Modify Records") to be Dark */
#     div[data-testid="stExpander"] summary p,
#     div[data-testid="stExpander"] summary span,
#     summary p {
#         /*color: #0f172a !important;*/ /* Dark Blue/Black */
#         font-weight: 800 !important;
#         font-size: 18px !important;
#     }

#     /* 2. Force Sidebar Menu Text to be Bright White */
#     section[data-testid="stSidebar"] div[data-testid="stRadio"] p,
#     section[data-testid="stSidebar"] label p {
#         /*color: #ffffff !important;*/
#         font-weight: 700 !important;
#         opacity: 1 !important; /* Removes Streamlit's default dimming */
#     }
            

#     /* ============================================================ */
#     /* 👇 NEW FIXES: Force specific missing elements to be DARK 👇 */
#     /* ============================================================ */

#     /* 1. Make TAB Text (Edit, Add, Delete) Dark */
#     button[data-baseweb="tab"] * {
#         /*color: #0f172a !important;*/ 
#         font-weight: 800 !important;
#     }
#     button[data-baseweb="tab"][aria-selected="true"] * {
#         /*color: #2563eb !important; */
#     }
    
#     /* 2. FORCE ALL INPUT LABELS TO BE DARK (Name, Age, Val, Unit, Range) */
#     div[data-testid="stVerticalBlock"] label *, div[data-testid="stForm"] label * {
#         /*color: #0f172a !important;*/ 
#         font-weight: 800 !important;
#     }

#     /* 3. Make PATIENT HEADER Text (Age, Gender) Dark */
#     .patient-header-text, .patient-header-text * {
#         /*color: #000000 !important;*/
#         font-weight: 800 !important;
#     }
            
#     /* 4. FORCE SIDEBAR MENU TEXT BACK TO WHITE */
#     section[data-testid="stSidebar"] label * {
#         /*color: #ffffff !important;*/
#         font-weight: 600 !important;
#     }
            
#     /* 5. Force the Expander Title ("Modify Records") to be Dark */
#     div[data-testid="stExpander"] summary * {
#         /* color: #0f172a !important; */
#         font-weight: 800 !important;
#     }
            





#     /* 7. CUSTOM INSTANT TOOLTIP */
#     .tbl-name {
#         position: relative;
#         display: inline-block;
#     }
    
#     .tbl-name .tooltiptext {
#         visibility: hidden;
#         background-color: #374151; /* Dark gray exactly like your screenshot */
#         /* color: #ffffff !important;*/
#         text-align: center;
#         border-radius: 6px;
#         padding: 6px 12px;
#         font-size: 13px;
#         font-weight: 600 !important;
#         position: absolute;
#         z-index: 50;
#         bottom: 120%; /* Positions it right above the text */
#         left: 0;
#         opacity: 0;
#         transition: opacity 0.2s ease-in-out;
#         white-space: nowrap;
#         box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
#     }

#     .tbl-name:hover .tooltiptext {
#         visibility: visible;
#         opacity: 1;
#     }

# </style>
# """, unsafe_allow_html=True)


# # --- 🎨 PRO MEDICAL DESIGN SYSTEM (AUTO-ADAPTIVE) ---
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;800&display=swap');
    
#     /* 1. GLOBAL SETTINGS */
#     html, body {
#         font-family: 'Manrope', sans-serif;
#         font-size: 16px; 
#     }

#     /* 2. DASHBOARD CARDS (Adaptive Background) */
#     .stat-card {
#         padding: 25px;
#         border-radius: 16px;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#         border: 1px solid rgba(128, 128, 128, 0.2); /* Soft transparent border */
#         transition: all 0.3s ease;
#     }
#     .stat-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2); }
#     .stat-val { font-size: 40px; font-weight: 800; }
#     .stat-label { font-size: 16px; font-weight: 600; text-transform: uppercase; opacity: 0.7; }

#     /* 3. CLINICAL REPORTS (FORMAL TABLE DESIGN) */
#     .report-table-header {
#         display: grid;
#         grid-template-columns: 4fr 1.5fr 1.5fr 2fr 1.5fr;
#         background-color: rgba(128, 128, 128, 0.15); /* Adapts to both light/dark */
#         padding: 12px 15px;
#         border-bottom: 2px solid rgba(128, 128, 128, 0.5);
#         margin-top: 15px;
#     }
#     .header-item {
#         font-size: 14px;
#         font-weight: 800;
#         text-transform: uppercase;
#         letter-spacing: 0.5px;
#     }

#     .report-table-row {
#         display: grid;
#         grid-template-columns: 4fr 1.5fr 1.5fr 2fr 1.5fr;
#         padding: 12px 15px;
#         border-bottom: 1px solid rgba(128, 128, 128, 0.2);
#         align-items: center;
#         transition: background 0.1s;
#     }
#     .report-table-row:hover {
#         background-color: rgba(128, 128, 128, 0.1);
#     }
    
#     /* Formal Text Styles */
#     .tbl-name { font-weight: 700; font-size: 16px; }
#     .tbl-val { font-weight: 700; font-size: 16px; }
#     .tbl-unit, .tbl-range { font-size: 14px; opacity: 0.8; }
    
#     /* Formal Status Text (Kept hardcoded because Red/Green is universal) */
#     .stat-txt-High { color: #ff4b4b !important; font-weight: 700; } /* Brighter red for visibility */
#     .stat-txt-Low { color: #faca2b !important; font-weight: 700; }  /* Brighter yellow/orange */
#     .stat-txt-Normal { color: #21c354 !important; font-weight: 600; } /* Brighter green */

#     /* Category Separator */
#     .category-header {
#         background-color: rgba(128, 128, 128, 0.2);
#         padding: 8px 15px;
#         font-weight: 800;
#         font-size: 14px;
#         border-bottom: 1px solid rgba(128, 128, 128, 0.4);
#         margin-top: 0px;
#     }

#     /* 4. BUTTONS (Explicit colors are fine here) */
#     div[data-testid="stButton"] button,
#     div[data-testid="stFormSubmitButton"] button {
#         background: #2563eb !important; 
#         border: none !important;
#         padding: 0.6rem 1.2rem !important;
#         border-radius: 8px !important;
#         font-weight: 700 !important;
#         width: 100% !important;
#         font-size: 16px !important;
#     }
#     div[data-testid="stButton"] button p,
#     div[data-testid="stFormSubmitButton"] button p {
#         color: white !important; /* Always white text on blue button */
#     }
#     div[data-testid="stButton"] button:hover,
#     div[data-testid="stFormSubmitButton"] button:hover {
#         background: #1e40af !important;
#     }

#     /* 5. INFO BOX & ALERTS */
#     .info-box-contrast {
#         border: 2px solid #3b82f6; 
#         padding: 20px;
#         border-radius: 10px;
#     }
#     .info-box-contrast h5 { color: #3b82f6 !important; font-weight: 800; font-size: 20px; }
#     .info-box-contrast p { font-size: 18px; }

#     /* 6. STRUCTURAL WEIGHT FIXES */
#     button[data-baseweb="tab"] * { font-weight: 800 !important; }
#     div[data-testid="stVerticalBlock"] label *, div[data-testid="stForm"] label * { font-weight: 800 !important; }
#     .patient-header-text, .patient-header-text * { font-weight: 800 !important; }
#     section[data-testid="stSidebar"] label * { font-weight: 600 !important; }
#     div[data-testid="stExpander"] summary * { font-weight: 800 !important; }

#     /* 7. CUSTOM INSTANT TOOLTIP */
#     .tbl-name {
#         position: relative;
#         display: inline-block;
#     }
#     .tbl-name .tooltiptext {
#         visibility: hidden;
#         background-color: #374151; 
#         color: #ffffff !important; /* Explicitly white so it shows on the dark tooltip background */
#         text-align: center;
#         border-radius: 6px;
#         padding: 6px 12px;
#         font-size: 13px;
#         font-weight: 600 !important;
#         position: absolute;
#         z-index: 50;
#         bottom: 120%; 
#         left: 0;
#         opacity: 0;
#         transition: opacity 0.2s ease-in-out;
#         white-space: nowrap;
#         box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
#     }
#     .tbl-name:hover .tooltiptext {
#         visibility: visible;
#         opacity: 1;
#     }
# </style>
# """, unsafe_allow_html=True)


# # --- POSITION: Top of app.py ---
# st.markdown("""
#     <style>
#     /* 1. Make the Expander itself transparent */
#     .stSidebar [data-testid="stExpander"] {
#         border: none !important;
#         background-color: transparent !important;
#         box-shadow: none !important;
#     }

#     /* 2. Format the "SYSTEM ADMIN" title */
#     .stSidebar [data-testid="stExpander"] summary p {
#         font-size: 15px !important;
#         /*color: #94a3b8 !important;*/
#         text-transform: uppercase;
#         font-weight: bold;
#     }

#     /* 3. Remove default Streamlit gaps between items */
#     .stSidebar [data-testid="stExpanderDetails"] {
#         display: flex;
#         flex-direction: column;
#         gap: 0px !important;
#         padding-top: 0px !important;
#         padding-bottom: 5px !important;
#     }

#     /* 4. Turn bulky buttons into a tight text list */
#     .stSidebar [data-testid="stExpanderDetails"] button {
#         background-color: transparent !important; 
#         border: none !important;                  
#         box-shadow: none !important;              
#        /* color: #cbd5e1 !important; */                
#         justify-content: flex-start !important;   
#         text-align: left !important;
#         width: 100% !important;
#         padding: 4px 10px !important;             
#         font-size: 13px !important;
#         margin: 0px !important;
#         min-height: 28px !important;
#     }

#     /* 5. Subtle hover effect for the list items */
#     .stSidebar [data-testid="stExpanderDetails"] button:hover {
#         background-color: rgba(255, 255, 255, 0.08) !important; 
#        /* color: #ffffff !important; */
#         border-radius: 4px !important;
#     }

#     /* 6. 🔥 TARGET THE CORRECT "stAlert" BOX TO FORCE 1-LINE */
#     .stSidebar [data-testid="stAlert"] {
#         padding: 2px 8px !important; /* Shrink the outer box */
#         min-height: 20px !important;
#         margin-bottom: 5px !important;
#         width: 100% !important;
#     }
    
#     /* Force the text inside the alert to stay on one line */
#     .stSidebar [data-testid="stAlert"] div,
#     .stSidebar [data-testid="stAlert"] p,
#     .stSidebar [data-testid="stAlert"] span {
#         white-space: nowrap !important; 
#         font-size: 15px !important;     
#         margin: 0px !important;
#         padding: 0px !important;
#         line-height: 1.5 !important;
#     }
#     </style>
# """, unsafe_allow_html=True)

# --- 🎨 PRO MEDICAL DESIGN SYSTEM (AUTO-ADAPTIVE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;800&display=swap');
    
    /* =========================================
       1. GLOBAL SETTINGS & MAIN DASHBOARD
       ========================================= */
    html, body {
        font-family: 'Manrope', sans-serif;
        font-size: 16px; 
    }

    /* Dashboard Cards (Adaptive Background) */
    .stat-card {
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2); 
        transition: all 0.3s ease;
    }
    .stat-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2); }
    .stat-val { font-size: 40px; font-weight: 800; }
    .stat-label { font-size: 16px; font-weight: 600; text-transform: uppercase; opacity: 0.7; }

    /* Clinical Reports (Formal Table Design) */
    .report-table-header {
        display: grid;
        grid-template-columns: 4fr 1.5fr 1.5fr 2fr 1.5fr;
        background-color: rgba(128, 128, 128, 0.15); 
        padding: 12px 15px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.5);
        margin-top: 15px;
    }
    .header-item {
        font-size: 14px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .report-table-row {
        display: grid;
        grid-template-columns: 4fr 1.5fr 1.5fr 2fr 1.5fr;
        padding: 12px 15px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        align-items: center;
        transition: background 0.1s;
    }
    .report-table-row:hover { background-color: rgba(128, 128, 128, 0.1); }
    
    /* Formal Text Styles */
    .tbl-name { font-weight: 700; font-size: 16px; }
    .tbl-val { font-weight: 700; font-size: 16px; }
    .tbl-unit, .tbl-range { font-size: 14px; opacity: 0.8; }
    
    /* Formal Status Text */
    .stat-txt-High { color: #ff4b4b !important; font-weight: 700; } 
    .stat-txt-Low { color: #faca2b !important; font-weight: 700; }  
    .stat-txt-Normal { color: #21c354 !important; font-weight: 600; } 

    /* Category Separator */
    .category-header {
        background-color: rgba(128, 128, 128, 0.2);
        padding: 8px 15px;
        font-weight: 800;
        font-size: 14px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.4);
        margin-top: 0px;
    }

    /* Buttons */
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button {
        background: #2563eb !important; 
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        width: 100% !important;
        font-size: 16px !important;
    }
    div[data-testid="stButton"] button p,
    div[data-testid="stFormSubmitButton"] button p { color: white !important; }
    div[data-testid="stButton"] button:hover,
    div[data-testid="stFormSubmitButton"] button:hover { background: #1e40af !important; }

    /* Info Box & Structural Fixes */
    .info-box-contrast { border: 2px solid #3b82f6; padding: 20px; border-radius: 10px; }
    .info-box-contrast h5 { color: #3b82f6 !important; font-weight: 800; font-size: 20px; }
    .info-box-contrast p { font-size: 18px; }
    
    button[data-baseweb="tab"] * { font-weight: 800 !important; }
    div[data-testid="stVerticalBlock"] label *, div[data-testid="stForm"] label * { font-weight: 800 !important; }
    .patient-header-text, .patient-header-text * { font-weight: 800 !important; }
    section[data-testid="stSidebar"] label * { font-weight: 600 !important; }
    div[data-testid="stExpander"] summary * { font-weight: 800 !important; }

    /* Custom Instant Tooltip */
    .tbl-name { position: relative; display: inline-block; }
    .tbl-name .tooltiptext {
        visibility: hidden;
        background-color: #374151; 
        color: #ffffff !important; 
        text-align: center;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 13px;
        font-weight: 600 !important;
        position: absolute;
        z-index: 50;
        bottom: 120%; 
        left: 0;
        opacity: 0;
        transition: opacity 0.2s ease-in-out;
        white-space: nowrap;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
    }
    .tbl-name:hover .tooltiptext { visibility: visible; opacity: 1; }

    /* =========================================
       2. SIDEBAR SYSTEM ADMIN FIXES
       ========================================= */
       
    /* Transparent Expander */
    .stSidebar [data-testid="stExpander"] {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* "SYSTEM ADMIN" Title (Adaptive Opacity) */
    .stSidebar [data-testid="stExpander"] summary p {
        font-size: 15px !important;
        text-transform: uppercase;
        font-weight: bold;
        opacity: 0.7; 
    }

    /* Remove gaps */
    .stSidebar [data-testid="stExpanderDetails"] {
        display: flex;
        flex-direction: column;
        gap: 0px !important;
        padding-top: 0px !important;
        padding-bottom: 5px !important;
    }

    /* Bulky buttons to text list (Adaptive Opacity) */
    .stSidebar [data-testid="stExpanderDetails"] button {
        background-color: transparent !important; 
        border: none !important;                  
        box-shadow: none !important;              
        justify-content: flex-start !important;   
        text-align: left !important;
        width: 100% !important;
        padding: 4px 10px !important;             
        font-size: 13px !important;
        margin: 0px !important;
        min-height: 28px !important;
        opacity: 0.8; 
    }

    /* Sidebar Hover Effect (Adaptive Grey Overlay) */
    .stSidebar [data-testid="stExpanderDetails"] button:hover {
        background-color: rgba(128, 128, 128, 0.2) !important; 
        border-radius: 4px !important;
        opacity: 1 !important;
    }

    /* Target stAlert Box to Force 1-Line */
    .stSidebar [data-testid="stAlert"] {
        padding: 2px 8px !important; 
        min-height: 20px !important;
        margin-bottom: 5px !important;
        width: 100% !important;
    }
    .stSidebar [data-testid="stAlert"] div,
    .stSidebar [data-testid="stAlert"] p,
    .stSidebar [data-testid="stAlert"] span {
        white-space: nowrap !important; 
        font-size: 15px !important;     
        margin: 0px !important;
        padding: 0px !important;
        line-height: 1.5 !important;
    }
</style>
""", unsafe_allow_html=True)
# --- LOGIC HELPERS ---
def get_greeting():
    h = datetime.datetime.now().hour
    if h < 12: return "Good Morning ☀️"
    elif h < 17: return "Good Afternoon 🌤️"
    else: return "Good Evening 🌙"

def get_stats():
    conn = sqlite3.connect("reportlens_lab.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM test_results")
    t = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM test_results WHERE status IN ('High', 'Low')")
    a = cursor.fetchone()[0]
    conn.close()
    return t, a


# --- SIDEBAR STATUS UPGRADE ---
online = is_connected()
status_dot = "4ade80" if online else "f59e0b" # Green if online, Orange if offline
status_text = "Smart Vision AI" if online else "Local Rules Active"

with st.sidebar:
    # ... (keep your existing image/title code) ...
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=70)
        st.title("ReportLens")
        st.markdown("<div style='color:#94a3b8; font-size:12px; margin-top:-10px'>MEDICAL INTELLIGENCE HUB</div>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("MAIN MENU", ["🏠 Dashboard", "👥 Patient Registry", "📄 Clinical Reports"], label_visibility="collapsed")
        st.markdown("---")
        # st.markdown("<div style='background:#0f172a; padding:10px; border-radius:8px; border:1px solid #334155'><span style='color:#4ade80'>●</span> <span style='color:white; font-weight:bold'>System Online</span></div>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style='background:#0f172a; padding:10px; border-radius:8px; border:1px solid #334155'>
            <span style='color:#{status_dot}'>●</span> 
            <span style='color:white; font-weight:bold'>{status_text}</span>
        </div>
    """, unsafe_allow_html=True)

# --- POSITION: Inside with st.sidebar: ---
with st.sidebar:
    st.markdown("---")
    
    with st.expander("⚙️ SYSTEM ADMIN"):
        
        # The single clean list item
        if st.button("🗑️ Factory Reset"):
            st.session_state["admin_action"] = "reset"

        # --- Confirmation Logic ---
        if st.session_state.get("admin_action") == "reset":
            st.warning("⚠️ Wipe DB & PDFs?")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes"):
                    # Wipes SQL and Deletes PDF files
                    db_manager.factory_reset_db()
                    st.session_state["admin_action"] = None
                    st.success("Cleaned")
                    time.sleep(1)
                    st.rerun()
            with c2:
                if st.button("❌ No"):
                    st.session_state["admin_action"] = None
                    st.rerun()
# =========================================================
# 1. DASHBOARD
# =========================================================
if menu == "🏠 Dashboard":
    st.markdown(f"# {get_greeting()}")
    st.markdown(f"#### 📅 {datetime.date.today().strftime('%A, %B %d, %Y')}")
    st.markdown("---")

    patients = get_all_patients()
    p_count = len(patients) if patients else 0
    t_count, a_count = get_stats()

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="stat-card"><div style="float:right; font-size:30px">👥</div><div class="stat-label">Total Patients</div><div class="stat-val" style="color:#4f46e5">{p_count}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="stat-card"><div style="float:right; font-size:30px">🧪</div><div class="stat-label">Tests Processed</div><div class="stat-val" style="color:#059669">{t_count}</div></div>""", unsafe_allow_html=True)
    with c3:
        color = "#dc2626" if a_count > 0 else "#94a3b8"
        icon = "⚠️" if a_count > 0 else "✅"
        st.markdown(f"""<div class="stat-card"><div style="float:right; font-size:30px">{icon}</div><div class="stat-label">Abnormal Findings</div><div class="stat-val" style="color:{color}">{a_count}</div></div>""", unsafe_allow_html=True)

    st.write("##")
    st.subheader("📥 Upload Report")
    
    with st.container():
        c_upload, c_info = st.columns([1, 2])
        with c_upload:
            st.markdown("""<div style="background:white; padding:25px; border:2px dashed #94a3b8; border-radius:10px; text-align:center;"><div style="font-size:32px; margin-bottom:5px">📄</div><div style="color:#0f172a; font-weight:600; font-size:16px;">Select Patient PDF File</div></div>""", unsafe_allow_html=True)
            #uploaded_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")

            # 👇 Added 'key' using session state
            uploaded_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed", key=f"uploader_{st.session_state['file_uploader_key']}")
            
            if uploaded_file:

                if st.button("🚀 Run Extraction"):
                    temp = "temp_upload.pdf"
                    with open(temp, "wb") as f: f.write(uploaded_file.getbuffer())
                    prog = st.progress(0)
                    status = st.empty()
                    
                    # Check status again at moment of click
                    online_mode = is_connected()
                    
                    try:
                        with st.spinner("Processing..."):
                            # Step 1: Always run OCR
                            status.markdown(f"**⏳ Step 1: OCR Extraction...**")
                            subprocess.run([sys.executable, "1_extract_ocr.py", temp], check=True)
                            prog.progress(25)

                            if online_mode:
                                # PATH A: INTERNET BASED
                                status.markdown(f"**🌐 Step 2: AI Text Splitting...**")
                                subprocess.run(["python", "2_split_text.py"], check=True)
                                prog.progress(50)
                                
                                status.markdown(f"**🧠 Step 3: Groq AI Extraction...**")
                                subprocess.run([sys.executable, "3_api_extraction.py"], check=True)
                                prog.progress(75)
                            else:
                                # PATH B: RULE BASED
                                status.markdown(f"**⚙️ Step 2: Rule-based Slicing...**")
                                subprocess.run(["python", "2_extract_data.py"], check=True)
                                prog.progress(50)
                                
                                status.markdown(f"**📋 Step 3: Regex JSON Formatting...**")
                                subprocess.run(["python", "3_json.py"], check=True)
                                prog.progress(75)

                            # Step 4: Always run DB Insert (Reads 'final_clean_output.json')
                            status.markdown(f"**🗄️ Step 4: Database Integration...**")
                            subprocess.run(["python", "4_insert_data.py"], check=True)
                            prog.progress(100)

                            status.success(f"✅ Extraction Complete ({'Cloud' if online_mode else 'Local'} Mode)")

    
                            try:
                                import json, shutil, os, sqlite3, datetime
                                with open("final_clean_output.json", "r", encoding="utf-8") as f:
                                    ext_data = json.load(f)

                                p_name = ext_data.get("patient_details", {}).get("name", "")
                                p_age = ext_data.get("patient_details", {}).get("age", 0)

                                # 1. Find the Patient ID
                                conn = sqlite3.connect("reportlens_lab.db")
                                cur = conn.cursor()
                                cur.execute("SELECT patient_id FROM patients WHERE name=? AND age=?", (p_name, p_age))
                                res = cur.fetchone()
                                conn.close()

                                if res:
                                    pid_db = res[0]
                                    
                                    # 🔥 FIX: Use SYSTEM DATE and TIME for a unique name
                                    # Example: 62_2026-03-10_143022.pdf
                                    now = datetime.datetime.now()
                                    timestamp = now.strftime("%Y-%m-%d_%H%M%S")
                                    
                                    os.makedirs("uploaded_reports", exist_ok=True)
                                    new_filename = f"uploaded_reports/{pid_db}_{timestamp}.pdf"
                                    
                                    # Copy the temporary file to the permanent history folder
                                    shutil.copy(temp, new_filename)


                            except Exception as save_err:
                                print(f"Error saving PDF: {save_err}")
                            # -------------------------------------------------------
                            st.session_state["file_uploader_key"] += 1
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        if os.path.exists(temp): os.remove(temp)
        with c_info:
            st.markdown("""<div class="info-box-contrast"><h5>💡 Automated Extraction</h5><p>Upload a medical PDF report. The system will automatically scan the document using OCR and extract lab results into the database.</p></div>""", unsafe_allow_html=True)

# =========================================================
# 2. PATIENT REGISTRY (FIXED SAVING & BUTTONS)
# =========================================================
elif menu == "👥 Patient Registry":
    c_h, c_s = st.columns([2, 1])
    with c_h: st.title("Patient Registry")
    with c_s: search = st.text_input("🔍 Search", "")

    patients = get_all_patients()
    if patients:
        df = pd.DataFrame(patients, columns=["ID", "Name", "Age", "Gender"])
        if search: df = df[df["Name"].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("### Manage Records")
        c1, c2 = st.columns([1, 2])
        with c1:
            pmap = {f"{r['Name']} (ID: {r['ID']})": r['ID'] for i, r in df.iterrows()}
            sel = st.selectbox("Select Patient", list(pmap.keys()))
            pid = pmap[sel]
        
        with c2:
            t1, t2 = st.tabs(["✏️ Edit Profile", "🗑️ Delete Record"])
            
            # --- TAB 1: EDIT (Fixes Saving Issue) ---
            with t1:
                cur = df[df["ID"]==pid].iloc[0]
                
                # Using st.form + unique keys ensures saving works
                with st.form(key=f"form_{pid}"):
                    st.caption(f"Editing: {cur['Name']}")
                    n = st.text_input("Name", value=cur["Name"])
                    
                    c_age, c_gen = st.columns(2)
                    curr_age = int(cur["Age"]) if cur["Age"] and str(cur["Age"]).isdigit() else 0
                    a = c_age.number_input("Age", value=curr_age, step=1)
                    
                    # Correct Gender Index
                    g_opts = ["Male", "Female", "Other"]
                    try:
                        g_idx = g_opts.index(cur["Gender"])
                    except:
                        g_idx = 0
                    g = c_gen.selectbox("Gender", g_opts, index=g_idx)
                    
                    if st.form_submit_button("💾 Save Changes"):
                        update_patient_metadata(pid, n, str(a), g)
                        st.success("✅ Saved!")
                        time.sleep(0.5)
                        st.rerun()

            # --- TAB 2: DELETE (Fixes Visibility) ---
            with t2:
                if st.button("🗑️ Request Delete", key=f"req_del_{pid}"):
                    st.session_state["confirm_delete_pid"] = pid
                    st.rerun()

                if st.session_state.get("confirm_delete_pid") == pid:
                    st.warning(f"Delete {cur['Name']}?")
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("✅ YES", key=f"yes_{pid}"):
                        delete_patient_completely(pid)
                        del st.session_state["confirm_delete_pid"]
                        st.success("Deleted")
                        time.sleep(1)
                        st.rerun()
                    if col_no.button("❌ CANCEL", key=f"no_{pid}"):
                        del st.session_state["confirm_delete_pid"]
                        st.rerun()

                      
# =========================================================
# 3. CLINICAL REPORTS (FORMAL TABLE DESIGN)
# =========================================================
elif menu == "📄 Clinical Reports":
    st.title("📄 Clinical Reports")
    
    patients = get_all_patients()
    if not patients:
        st.warning("No patients found.")
        st.stop()
        
    patients = list(reversed(patients))
    pmap = {f"{p[1]}": p[0] for p in patients}
    sel = st.selectbox("Select Patient", list(pmap.keys()))
    pid = pmap[sel]
    curr = next(p for p in patients if p[0]==pid)

    # --- PREPARE PDF VIEWER & EYE ICON ---
    import os
    import base64
    
    pdf_html = ""
    results = get_patient_report(pid)
    
    if results:
        latest_date = results[0][1]
        safe_date = latest_date.replace("/", "-")
        
        pdf_path = None
        if os.path.exists("uploaded_reports"):
            # 1. Find all files starting with "PatientID_"
            matching_files = [f for f in os.listdir("uploaded_reports") if f.startswith(f"{pid}_")]
            
            if matching_files:
                # 2. 🔥 Sort by 'File Creation Time' to get the one you JUST uploaded
                matching_files.sort(key=lambda x: os.path.getmtime(os.path.join("uploaded_reports", x)), reverse=True)
                pdf_path = os.path.join("uploaded_reports", matching_files[0])

        # Now the eye icon will always open the correct file!
                

        if pdf_path:
            import os
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            
            if file_size_mb < 2.0:
                # FAST MODE: If file is small, use your original method
                with open(pdf_path, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')

                # 🔥 THE FIX: Using <embed> instead of <iframe> to bypass cloud security blocks
                viewer_content = f'<embed src="data:application/pdf;base64,{base64_pdf}#toolbar=1&view=FitH" type="application/pdf" width="100%" height="100%" style="flex-grow: 1; border:none;">'
                
            else:
                # LARGE FILE MODE: Convert pages to images so the browser doesn't crash
                import fitz  # This is PyMuPDF
                import base64
                
                doc = fitz.open(pdf_path)
                img_html = "<div style='overflow-y: auto; height: 100%; width: 100%; background: #525659; text-align: center; padding: 20px 0;'>"
                
                # Loop through the PDF and turn each page into a picture
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=120) 
                    img_base64 = base64.b64encode(pix.tobytes("png")).decode('utf-8')
                    img_html += f'<img src="data:image/png;base64,{img_base64}" style="max-width: 95%; margin-bottom: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);"><br>'
                    
                img_html += "</div>"
                viewer_content = img_html

            # --- Inject the chosen viewer into your custom Eye Icon Modal ---
            pdf_html = f"""
<style>
    #modal-toggle {{ display: none; }}
    .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.6); z-index: 99998; }}
    .modal-content {{ display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 75vw; height: 85vh; background: white; z-index: 99999; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); overflow: hidden; flex-direction: column; }}
    #modal-toggle:checked ~ .modal-overlay {{ display: block; }}
    #modal-toggle:checked ~ .modal-content {{ display: flex; }}
</style>

<div style="position:absolute; top:20px; right:20px; z-index:100;">
    <label for="modal-toggle" style="cursor:pointer; font-size:28px;" title="View original record">👁️</label>
</div>

<input type="checkbox" id="modal-toggle">
<label for="modal-toggle" class="modal-overlay"></label>

<div class="modal-content">
    <div style="background:#1e293b; color:white; padding:12px 20px; font-weight:bold; font-size:16px; display:flex; justify-content:space-between; align-items:center;">
        <span>📄 Original Lab Report ({latest_date})</span>
        <label for="modal-toggle" style="cursor:pointer; font-size:14px; background:#ef4444; color:white; padding:6px 14px; border-radius:6px; font-weight:bold; letter-spacing:0.5px;" title="Close Report">✖</label>
    </div>
    {viewer_content}
</div>
            """

    # Patient Banner (Injecting the HTML correctly with .strip() to remove extra spaces)
    st.markdown(f"""
    <div style="position:relative; background:#f1f5f9; padding:20px; border-radius:12px; border-left:6px solid #4f46e5; margin-bottom:20px;">
        <h2 style="margin:0; color:#000000; font-weight:800; font-size:32px">{curr[1]}</h2>
        <div style="margin-top:5px; font-size:20px; display: flex; gap: 20px; align-items: center;">
            <span class="patient-header-text">🎂 {curr[2]} Years</span>
            <span class="patient-header-text">⚧ {curr[3]}</span>
            <span class="patient-header-text">🆔 #{curr[0]}</span>
        </div>
        {pdf_html.strip()}
    </div>
    """, unsafe_allow_html=True)

    if results:
        #results.sort(key=lambda x: (x[2], x[3], x[1]))
        # Change Line 539 to this:
        results.sort(key=lambda x: (x[2], datetime.datetime.strptime(x[1], '%d-%m-%y'), x[3]), reverse=True)
        # --- FORMAL HEADER ---
        st.markdown("""
        <div class="report-table-header">
            <div class="header-item">Test Name</div>
            <div class="header-item">Value</div>
            <div class="header-item">Unit</div>
            <div class="header-item">Reference</div>
            <div class="header-item">Status</div>
        </div>
        """, unsafe_allow_html=True)

       

        curr_cat = None
        for row in results:
            rid, rdate, cat, name, val, unit, ref, status = row
            
            # --- POSITION A: Category Divider ---
            if cat != curr_cat:
                st.markdown(f"""<div class="category-header">{cat}</div>""", unsafe_allow_html=True)
                curr_cat = cat
            
            # --- POSITION B: Status Style ---
            status_cls = "stat-txt-Normal"
            if status == "High": status_cls = "stat-txt-High"
            elif status == "Low": status_cls = "stat-txt-Low"
            
            # --- POSITION C: Table Row (Added Date into the Name Column) ---
            st.markdown(f"""
            <div class="report-table-row">
                <div class="tbl-name">
                    {name} <span style="color: #64748b; font-weight: 450; font-size: 13px; margin-left: 8px;">({rdate})</span>
                    <span class="tooltiptext">{rdate}</span>
                </div>
                <div class="tbl-val">{val}</div>
                <div class="tbl-unit">{unit}</div>
                <div class="tbl-range">{ref}</div>
                <div class="{status_cls}">{status}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No records found.")
        results = []

    st.markdown("---")
    
    # ACTIONS
    with st.expander("⚡ Modify Records"):
        t1, t2, t3 = st.tabs(["📝 Edit", "➕ Add", "❌ Delete"])
        with t1:
            if results:
                rmap = {f"{r[3]} ({r[4]})": r for r in results}
                rc = st.selectbox("Select Result", list(rmap.keys()))
                if rc:
                    rec = rmap[rc]
                    with st.form("ed"):
                        c1, c2 = st.columns(2)
                        v = c1.text_input("Val", rec[4]); u = c2.text_input("Unit", rec[5])
                        r = c1.text_input("Range", rec[6]); s = c2.selectbox("Status", ["Normal", "High", "Low", "N/A"], index=0)
                        if st.form_submit_button("💾 Update"): update_test_record(rec[0], v, u, r, s); st.rerun()
        with t2:
            with st.form("ad"):
                d = st.text_input("Date", str(datetime.date.today())); cat = st.text_input("Cat", "HEMATOLOGY"); nm = st.text_input("Name")
                c1, c2 = st.columns(2)
                v = c1.text_input("Val"); u = c2.text_input("Unit"); r = c1.text_input("Range"); s = c2.selectbox("Status", ["Normal", "High", "Low"])
                if st.form_submit_button("💾 Add Record"): add_manual_test_record(pid, d, cat, nm, v, u, r, s); st.rerun()
        with t3:
            if results:
                dk = st.selectbox("Select Result", list(rmap.keys()), key="dk")
                if st.button("🗑️ Request Delete"): st.session_state["confirm_delete_rid"] = rmap[dk][0]; st.rerun()
                if st.session_state.get("confirm_delete_rid") == rmap[dk][0]:
                    if st.button("✅ Confirm Delete"): delete_test_record(rmap[dk][0]); del st.session_state["confirm_delete_rid"]; st.rerun()
                    if st.button("❌ Cancel"): del st.session_state["confirm_delete_rid"]; st.rerun()



                    