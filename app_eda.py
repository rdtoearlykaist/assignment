import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase configuration
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "Not specified"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# Home page
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home: Population Trends EDA App")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')} welcome!")
        st.markdown("""
        ---
        **Population Trends Analysis App**  
        - Dataset: population_trends.csv  
        - Features: missing value handling, national trend, regional 5-year change, change rate, top changes, cumulative area chart
        """)

# Authentication pages: Login, Register, FindPassword, UserInfo, Logout
class Login:
    def __init__(self):
        st.title("🔐 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']
                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "Not specified")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")
                st.success("Login successful!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("Login failed")

class Register:
    def __init__(self, login_page_url):
        st.title("📝 Register")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        name = st.text_input("Name")
        gender = st.selectbox("Gender", ["Not specified", "Male", "Female"])
        phone = st.text_input("Phone")
        if st.button("Sign Up"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("Registration successful! Redirecting to login...")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("Registration failed")

class FindPassword:
    def __init__(self):
        st.title("🔎 Reset Password")
        email = st.text_input("Email")
        if st.button("Send Reset Email"):
            try:
                auth.send_password_reset_email(email)
                st.success("Reset email sent!")
                time.sleep(1)
                st.rerun()
            except:
                st.error("Failed to send email")

class UserInfo:
    def __init__(self):
        st.title("👤 User Info")
        email = st.session_state.get("user_email", "")
        new_email = st.text_input("Email", value=email)
        name = st.text_input("Name", value=st.session_state.get("user_name", ""))
        gender = st.selectbox("Gender", ["Not specified", "Male", "Female"],
                              index=["Not specified", "Male", "Female"].index(st.session_state.get("user_gender", "Not specified")))
        phone = st.text_input("Phone", value=st.session_state.get("user_phone", ""))
        uploaded_file = st.file_uploader("Profile Image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)
        if st.button("Update"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone
            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })
            st.success("User info updated.")
            time.sleep(1)
            st.rerun()

class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "Not specified"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("Logged out.")
        time.sleep(1)
        st.rerun()

# EDA page
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv.")
            return
        df = pd.read_csv(uploaded)
        # Handle missing and convert types
        df.loc[df['지역']=='세종', ['인구','출생아수(명)','사망자수(명)']] = \
            df.loc[df['지역']=='세종', ['인구','출생아수(명)','사망자수(명)']].replace('-', 0)
        df[['인구','출생아수(명)','사망자수(명)']] = df[['인구','출생아수(명)','사망자수(명)']].apply(pd.to_numeric, errors='coerce')
        tabs = st.tabs(["Basic Stats","National Trend","Regional Change","Top Changes","Area Chart"])

        # Tab 3: Regional Change
        with tabs[2]:
            st.header("Regional 5-Year Change")
            mapping = {
                '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon','광주':'Gwangju',
                '대전':'Daejeon','울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi','강원':'Gangwon',
                '충북':'North Chungcheong','충남':'South Chungcheong','전북':'North Jeolla',
                '전남':'South Jeolla','경북':'North Gyeongsang','경남':'South Gyeongsang','제주':'Jeju'
            }
            latest = df['연도'].max()
            past5 = latest - 5
            df_latest = df[df['연도']==latest]
            df_past = df[df['연도']==past5]
            merged = pd.merge(df_latest[['지역','인구']], df_past[['지역','인구']], on='지역', suffixes=('_now','_past'))
            merged = merged[merged['지역']!='전국']
            merged['region_en'] = merged['지역'].map(mapping)
            merged['change'] = merged['인구_now'] - merged['인구_past']
            merged['change_k'] = merged['change']/1000
            merged_sorted = merged.sort_values('change_k', ascending=False)
            fig, ax = plt.subplots()
            sns.barplot(x='change_k', y='region_en', data=merged_sorted, ax=ax)
            ax.set_title("5-Year Pop Change by Region")
            ax.set_xlabel("Change (thousands)")
            ax.set_ylabel("")
            for i, (_, row) in enumerate(merged_sorted.iterrows()):
                ax.text(row['change_k'], i, f"{row['change_k']:.1f}")
            st.pyplot(fig)
            st.markdown("Each bar shows the absolute population change over the past five years for each region (excluding nationwide).")

            # Change rate
            merged['rate'] = (merged['change']/merged['인구_past'])*100
            merged['rate'] = merged['rate'].round(1)
            rate_sorted = merged.sort_values('rate', ascending=False)
            fig2, ax2 = plt.subplots()
            sns.barplot(x='rate', y='region_en', data=rate_sorted, ax=ax2)
            ax2.set_title("5-Year Change Rate by Region")
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("")
            for i, (_, row) in enumerate(rate_sorted.iterrows()):
                ax2.text(row['rate'], i, f"{row['rate']}%")
            st.pyplot(fig2)
            st.markdown("This chart shows the percentage change relative to five years ago.")

# Navigation
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]
selected_page = st.navigation(pages)
selected_page.run()