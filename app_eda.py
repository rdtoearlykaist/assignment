import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정 (기존 유지)
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

# ---------------------
# 세션 상태 초기화 (기존 유지)
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스 (수정)
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home: Population Trends EDA App")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        ---
        **Population Trends Analysis App**  
        - 데이터셋: population_trends.csv  
        - 내용: 연도별 및 지역별 인구 추이를 분석하는 Streamlit EDA 앱  
        - 기능: 결측치/중복 확인, 연도별 전국 인구 추이, 지역별 변화량 및 변화율 분석, 증감 상위 사례 도출, 누적 영역 그래프 생성  
        """)

# ---------------------
# 로그인/회원가입/비번찾기/사용자정보/로그아웃 페이지 클래스 (기존 유지)
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
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
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
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

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스 (수정)
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        # 결측치 및 데이터 타입 변환
        df.loc[df['지역']=='세종', ['인구','출생아수(명)','사망자수(명)']] = df[df['지역']=='세종'][['인구','출생아수(명)','사망자수(명)']].replace('-', 0)
        df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
        df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce')
        df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce')

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        # Tab 1: 기초 통계
        with tabs[0]:
            st.header("🔍 기초 통계 및 데이터 구조")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.subheader("데이터프레임 정보")
            st.text(buffer.getvalue())
            st.subheader("기초 통계량")
            st.dataframe(df.describe())
            st.subheader("결측치 및 중복")
            missing = df.isnull().sum()
            st.write(missing)
            duplicates = df.duplicated().sum()
            st.write(f"- 중복 행 개수: {duplicates}개")

        # Tab 2: 연도별 전국 인구 추이
        with tabs[1]:
            st.header("📈 연도별 전국 인구 추이")
            nation = df[df['지역']=='전국']
            fig, ax = plt.subplots()
            ax.plot(nation['연도'], nation['인구'], marker='o')
            ax.set_title("Nationwide Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

            # 2035년 예측
            recent = nation.sort_values('연도').tail(3)
            avg_birth = recent['출생아수(명)'].mean()
            avg_death = recent['사망자수(명)'].mean()
            last_year = nation['연도'].max()
            last_pop = nation[nation['연도']==last_year]['인구'].values[0]
            years_ahead = 2035 - last_year
            predict = last_pop + years_ahead * (avg_birth - avg_death)
            ax.plot([last_year, 2035], [last_pop, predict], linestyle='--', marker='x')
            st.pyplot(fig)

        # Tab 3: 지역별 분석
        with tabs[2]:
            st.header("🏙️ 지역별 인구 변화량 순위")
            latest = df['연도'].max()
            past = latest - 5
            df_latest = df[df['연도']==latest]
            df_past = df[df['연도']==past]
            merged = pd.merge(
                df_latest[['지역','인구']],
                df_past[['지역','인구']],
                on='지역',
                suffixes=('_latest','_past')
            )
            merged = merged[merged['지역']!='전국']
            merged['변화량'] = merged['인구_latest'] - merged['인구_past']
            merged_sorted = merged.sort_values('변화량', ascending=False)
            fig2, ax2 = plt.subplots()
            sns.barplot(x='변화량', y='지역', data=merged_sorted, ax=ax2)
            for idx, row in merged_sorted.iterrows():
                ax2.text(row['변화량'], idx, int(row['변화량']), va='center')
            st.pyplot(fig2)

            merged['변화율(%)'] = merged['변화량'] / merged['인구_past'] * 100
            merged_rate = merged.sort_values('변화율(%)', ascending=False)
            fig3, ax3 = plt.subplots()
            sns.barplot(x='변화율(%)', y='지역', data=merged_rate, ax=ax3)
            ax3.set_xlabel("Change Rate (%)")
            st.pyplot(fig3)

        # Tab 4: 변화량 분석
        with tabs[3]:
            st.header("🔢 증감률 상위 지역 및 연도")
            df_sorted = df.sort_values(['지역','연도'])
            df_sorted['diff'] = df_sorted.groupby('지역')['인구'].diff()
            df_diff = df_sorted[df_sorted['지역']!='전국'].dropna(subset=['diff'])
            top100 = df_diff.nlargest(100, 'diff')[['지역','연도','diff']]
            st.dataframe(top100.style.background_gradient(cmap='Blues', subset=['diff']))

        # Tab 5: 시각화
        with tabs[4]:
            st.header("🎨 누적 영역 그래프")
            pivot = df[df['지역']!='전국'].pivot(index='연도', columns='지역', values='인구')
            fig4, ax4 = plt.subplots()
            pivot.plot.area(ax=ax4, legend=False)
            ax4.set_title("Population by Region Area Chart")
            ax4.set_xlabel("Year")
            ax4.set_ylabel("Population")
            st.pyplot(fig4)

# ---------------------
# 페이지 객체 생성 및 네비게이션 실행 (기존 유지)
# ---------------------
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