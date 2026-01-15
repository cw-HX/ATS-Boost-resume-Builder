"""
ATS CV Generator - Streamlit Frontend
Main application entry point.
"""
import streamlit as st
from config import config
from api_client import api_client

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.APP_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        background-color: #cce5ff;
        border: 1px solid #b8daff;
        border-radius: 0.25rem;
        color: #004085;
    }
    .ats-score {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
    }
    .ats-score-high {
        color: #28a745;
    }
    .ats-score-medium {
        color: #ffc107;
    }
    .ats-score-low {
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)


def show_login_page():
    """Display login page."""
    st.markdown('<h1 class="main-header">📄 ATS CV Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate ATS-optimized CVs tailored to job descriptions</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.subheader("Login to Your Account")
            
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password", placeholder="Your password")
                
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.error("Please fill in all fields")
                    else:
                        try:
                            with st.spinner("Logging in..."):
                                api_client.login(email, password)
                            st.success("Login successful!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Login failed: {str(e)}")
        
        with tab2:
            st.subheader("Create New Account")
            
            st.info("**Password requirements:** Min 8 characters, including uppercase, lowercase, digit, and special character (!@#$%^&*)")
            
            with st.form("signup_form"):
                new_email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
                new_password = st.text_input("Password", type="password", placeholder="Create a strong password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                submit = st.form_submit_button("Sign Up", use_container_width=True)
                
                if submit:
                    if not new_email or not new_password or not confirm_password:
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters")
                    else:
                        try:
                            with st.spinner("Creating account..."):
                                api_client.signup(new_email, new_password)
                            st.success("Account created successfully! Please log in.")
                        except Exception as e:
                            st.error(f"Signup failed: {str(e)}")


def show_sidebar():
    """Display sidebar navigation."""
    with st.sidebar:
        st.markdown("### 👤 " + st.session_state.get(config.USER_KEY, {}).get("email", "User"))
        st.divider()
        
        # Navigation
        pages = {
            "🏠 Dashboard": "dashboard",
            "👤 Profile": "profile",
            "📝 Generate CV": "generate",
            "📜 CV History": "history",
        }
        
        for page_name, page_key in pages.items():
            if st.button(page_name, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state["current_page"] = page_key
                st.rerun()
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            api_client.logout()
            st.rerun()


def show_dashboard():
    """Display dashboard page."""
    st.header("🏠 Dashboard")
    
    # Check if profile exists
    try:
        profile = api_client.get_profile()
        has_profile = profile is not None
    except:
        has_profile = False
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Profile Status",
            value="✅ Complete" if has_profile else "❌ Incomplete"
        )
    
    with col2:
        try:
            history = api_client.get_cv_history(limit=100)
            cv_count = len(history)
        except:
            cv_count = 0
        st.metric(label="CVs Generated", value=cv_count)
    
    with col3:
        if history:
            latest_score = history[0].get("ats_score", 0)
        else:
            latest_score = "-"
        st.metric(label="Latest ATS Score", value=latest_score)
    
    st.divider()
    
    if not has_profile:
        st.warning("⚠️ Please complete your profile before generating CVs.")
        if st.button("Go to Profile", use_container_width=True):
            st.session_state["current_page"] = "profile"
            st.rerun()
    else:
        st.success("✅ Your profile is complete. You can generate CVs!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 Generate New CV", use_container_width=True):
                st.session_state["current_page"] = "generate"
                st.rerun()
        
        with col2:
            if st.button("👤 Update Profile", use_container_width=True):
                st.session_state["current_page"] = "profile"
                st.rerun()
    
    # Recent CVs
    if cv_count > 0:
        st.subheader("Recent CVs")
        
        for cv in history[:5]:
            with st.expander(f"📄 CV - ATS Score: {cv['ats_score']}% | {cv['created_at'][:10]}"):
                st.text(cv['job_description'][:200] + "..." if len(cv['job_description']) > 200 else cv['job_description'])
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("View", key=f"view_{cv['_id']}"):
                        st.session_state["selected_cv"] = cv['_id']
                        st.session_state["current_page"] = "view_cv"
                        st.rerun()


def show_profile_page():
    """Display profile management page."""
    st.header("👤 Profile Management")
    
    # Load existing profile
    try:
        profile = api_client.get_profile()
    except:
        profile = None
    
    tabs = st.tabs([
        "📋 Personal Details",
        "🎓 Education",
        "💻 Skills",
        "🚀 Projects",
        "💼 Internships",
        "📜 Certifications",
        "🏆 Achievements"
    ])
    
    # Personal Details Tab
    with tabs[0]:
        st.subheader("Personal Details")
        
        with st.form("personal_details_form"):
            pd = profile.get("personal_details", {}) if profile else {}
            
            full_name = st.text_input("Full Name*", value=pd.get("full_name", ""))
            location = st.text_input("Location", value=pd.get("location", ""))
            phone = st.text_input("Phone", value=pd.get("phone", ""))
            email = st.text_input("Email*", value=pd.get("email", st.session_state.get(config.USER_KEY, {}).get("email", "")))
            linkedin = st.text_input("LinkedIn URL", value=pd.get("linkedin", ""))
            github = st.text_input("GitHub URL", value=pd.get("github", ""))
            
            if st.form_submit_button("Save Personal Details", use_container_width=True):
                if not full_name or not email:
                    st.error("Full Name and Email are required")
                else:
                    try:
                        personal_data = {
                            "personal_details": {
                                "full_name": full_name,
                                "location": location,
                                "phone": phone,
                                "email": email,
                                "linkedin": linkedin,
                                "github": github
                            }
                        }
                        
                        if profile:
                            api_client.update_profile(personal_data)
                        else:
                            # Create new profile with default values
                            full_profile = {
                                "personal_details": personal_data["personal_details"],
                                "education": [],
                                "skills": {
                                    "programming_languages": [],
                                    "technical_skills": [],
                                    "developer_tools": []
                                },
                                "projects": [],
                                "internships": [],
                                "certifications": [],
                                "achievements": []
                            }
                            api_client.create_profile(full_profile)
                        
                        st.success("Personal details saved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving: {str(e)}")
    
    # Education Tab
    with tabs[1]:
        st.subheader("Education")
        
        education_list = profile.get("education", []) if profile else []
        
        # Display existing entries
        for i, edu in enumerate(education_list):
            with st.expander(f"🎓 {edu.get('degree', 'Degree')} - {edu.get('college_name', 'College')}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**College:** {edu.get('college_name', '')}")
                    st.write(f"**Degree:** {edu.get('degree', '')}")
                    st.write(f"**CGPA/Percentage:** {edu.get('cgpa_or_percentage', '')}")
                    st.write(f"**Session:** {edu.get('session_year', '')}")
                
                with col2:
                    if st.button("🗑️ Delete", key=f"del_edu_{i}"):
                        try:
                            api_client.delete_education(i)
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
        
        # Add new education
        st.divider()
        st.write("**Add New Education**")
        
        with st.form("add_education_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                college_name = st.text_input("College/University Name*")
                degree = st.text_input("Degree*")
            
            with col2:
                cgpa = st.text_input("CGPA/Percentage")
                session_year = st.text_input("Session Year* (e.g., 2020-2024)")
            
            if st.form_submit_button("Add Education", use_container_width=True):
                if not college_name or not degree or not session_year:
                    st.error("Please fill required fields")
                else:
                    try:
                        api_client.add_education({
                            "college_name": college_name,
                            "degree": degree,
                            "cgpa_or_percentage": cgpa,
                            "session_year": session_year
                        })
                        st.success("Education added!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    
    # Skills Tab
    with tabs[2]:
        st.subheader("Skills")
        
        skills = profile.get("skills", {}) if profile else {}
        
        with st.form("skills_form"):
            st.write("Enter skills separated by commas")
            
            prog_langs = st.text_area(
                "Programming Languages",
                value=", ".join(skills.get("programming_languages", [])),
                placeholder="Python, JavaScript, Java, C++"
            )
            
            tech_skills = st.text_area(
                "Technical Skills",
                value=", ".join(skills.get("technical_skills", [])),
                placeholder="Machine Learning, Web Development, Data Analysis"
            )
            
            dev_tools = st.text_area(
                "Developer Tools",
                value=", ".join(skills.get("developer_tools", [])),
                placeholder="Git, Docker, VS Code, AWS"
            )
            
            if st.form_submit_button("Save Skills", use_container_width=True):
                try:
                    skills_data = {
                        "programming_languages": [s.strip() for s in prog_langs.split(",") if s.strip()],
                        "technical_skills": [s.strip() for s in tech_skills.split(",") if s.strip()],
                        "developer_tools": [s.strip() for s in dev_tools.split(",") if s.strip()]
                    }
                    api_client.update_skills(skills_data)
                    st.success("Skills saved!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
    
    # Projects Tab
    with tabs[3]:
        st.subheader("Projects")
        
        projects = profile.get("projects", []) if profile else []
        
        for i, proj in enumerate(projects):
            with st.expander(f"🚀 {proj.get('project_name', 'Project')}", expanded=False):
                st.write(f"**Name:** {proj.get('project_name', '')}")
                if proj.get("project_link"):
                    st.write(f"**Link:** {proj.get('project_link', '')}")
                st.write(f"**Tech Stack:** {', '.join(proj.get('tech_stack', []))}")
                st.write("**Bullet Points:**")
                for bp in proj.get("bullet_points", []):
                    st.write(f"• {bp}")
                
                if st.button("🗑️ Delete", key=f"del_proj_{i}"):
                    try:
                        api_client.delete_project(i)
                        st.success("Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        
        st.divider()
        st.write("**Add New Project**")
        
        with st.form("add_project_form"):
            project_name = st.text_input("Project Name*")
            project_link = st.text_input("Project Link (optional)")
            tech_stack = st.text_input("Tech Stack (comma-separated)")
            bullet_points = st.text_area("Bullet Points (one per line)", height=150)
            
            if st.form_submit_button("Add Project", use_container_width=True):
                if not project_name:
                    st.error("Project name is required")
                else:
                    try:
                        bullets = [b.strip() for b in bullet_points.split("\n") if b.strip()]
                        techs = [t.strip() for t in tech_stack.split(",") if t.strip()]
                        
                        api_client.add_project({
                            "project_name": project_name,
                            "project_link": project_link,
                            "tech_stack": techs,
                            "bullet_points": bullets
                        })
                        st.success("Project added!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    
    # Internships Tab
    with tabs[4]:
        st.subheader("Internships")
        
        internships = profile.get("internships", []) if profile else []
        
        for i, intern in enumerate(internships):
            with st.expander(f"💼 {intern.get('internship_name', 'Internship')} at {intern.get('company_name', 'Company')}", expanded=False):
                st.write(f"**Role:** {intern.get('internship_name', '')}")
                st.write(f"**Company:** {intern.get('company_name', '')}")
                st.write("**Bullet Points:**")
                for bp in intern.get("bullet_points", []):
                    st.write(f"• {bp}")
                
                if st.button("🗑️ Delete", key=f"del_intern_{i}"):
                    try:
                        api_client.delete_internship(i)
                        st.success("Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        
        st.divider()
        st.write("**Add New Internship**")
        
        with st.form("add_internship_form"):
            intern_name = st.text_input("Internship Title/Role*")
            company_name = st.text_input("Company Name*")
            intern_bullets = st.text_area("Bullet Points (one per line)", height=150)
            
            if st.form_submit_button("Add Internship", use_container_width=True):
                if not intern_name or not company_name:
                    st.error("Please fill required fields")
                else:
                    try:
                        bullets = [b.strip() for b in intern_bullets.split("\n") if b.strip()]
                        
                        api_client.add_internship({
                            "internship_name": intern_name,
                            "company_name": company_name,
                            "bullet_points": bullets
                        })
                        st.success("Internship added!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    
    # Certifications Tab
    with tabs[5]:
        st.subheader("Certifications")
        
        certifications = profile.get("certifications", []) if profile else []
        
        for i, cert in enumerate(certifications):
            with st.expander(f"📜 {cert.get('certificate_name', 'Certificate')}", expanded=False):
                st.write(f"**Certificate:** {cert.get('certificate_name', '')}")
                st.write(f"**Issuer:** {cert.get('issuing_company', '')}")
                if cert.get("bullet_points"):
                    st.write("**Details:**")
                    for bp in cert.get("bullet_points", []):
                        st.write(f"• {bp}")
                
                if st.button("🗑️ Delete", key=f"del_cert_{i}"):
                    try:
                        api_client.delete_certification(i)
                        st.success("Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        
        st.divider()
        st.write("**Add New Certification**")
        
        with st.form("add_cert_form"):
            cert_name = st.text_input("Certificate Name*")
            issuing_company = st.text_input("Issuing Organization*")
            cert_bullets = st.text_area("Details (one per line, optional)")
            
            if st.form_submit_button("Add Certification", use_container_width=True):
                if not cert_name or not issuing_company:
                    st.error("Please fill required fields")
                else:
                    try:
                        bullets = [b.strip() for b in cert_bullets.split("\n") if b.strip()]
                        
                        api_client.add_certification({
                            "certificate_name": cert_name,
                            "issuing_company": issuing_company,
                            "bullet_points": bullets
                        })
                        st.success("Certification added!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    
    # Achievements Tab
    with tabs[6]:
        st.subheader("Achievements")
        
        achievements = profile.get("achievements", []) if profile else []
        
        for i, achievement in enumerate(achievements):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"🏆 {achievement}")
            
            with col2:
                if st.button("🗑️", key=f"del_ach_{i}"):
                    try:
                        api_client.delete_achievement(i)
                        st.success("Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        
        st.divider()
        st.write("**Add New Achievement**")
        
        with st.form("add_achievement_form"):
            new_achievement = st.text_input("Achievement")
            
            if st.form_submit_button("Add Achievement", use_container_width=True):
                if not new_achievement:
                    st.error("Please enter an achievement")
                else:
                    try:
                        api_client.add_achievement(new_achievement)
                        st.success("Achievement added!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


def show_generate_cv_page():
    """Display CV generation page."""
    st.header("📝 Generate ATS-Optimized CV")
    
    # Check profile
    try:
        profile = api_client.get_profile()
        if not profile:
            st.warning("⚠️ Please complete your profile first.")
            if st.button("Go to Profile"):
                st.session_state["current_page"] = "profile"
                st.rerun()
            return
    except Exception as e:
        st.error(f"Error loading profile: {str(e)}")
        return
    
    st.info("📌 Paste a job description below. Our AI will analyze it and generate an ATS-optimized CV tailored to this specific job.")
    
    job_description = st.text_area(
        "Job Description*",
        height=300,
        placeholder="Paste the complete job description here..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Analyze ATS Compatibility", use_container_width=True):
            if not job_description or len(job_description) < 50:
                st.error("Please enter a valid job description (at least 50 characters)")
            else:
                try:
                    with st.spinner("Analyzing..."):
                        analysis = api_client.analyze_ats(job_description)
                    
                    # Display analysis
                    score = analysis.get("score", 0)
                    score_class = "high" if score >= 90 else "medium" if score >= 70 else "low"
                    
                    st.markdown(f'<p class="ats-score ats-score-{score_class}">{score}%</p>', unsafe_allow_html=True)
                    st.write(f"**Keyword Match:** {analysis.get('keyword_match_percentage', 0)}%")
                    
                    st.write("**Matched Skills:**")
                    st.write(", ".join(analysis.get("aligned_skills", [])[:10]))
                    
                    st.write("**Missing Keywords:**")
                    st.write(", ".join(analysis.get("missing_keywords", [])[:10]))
                    
                    st.write("**Recommendations:**")
                    for rec in analysis.get("recommendations", []):
                        st.write(f"• {rec}")
                        
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
    
    with col2:
        if st.button("🚀 Generate CV", use_container_width=True, type="primary"):
            if not job_description or len(job_description) < 50:
                st.error("Please enter a valid job description (at least 50 characters)")
            else:
                try:
                    with st.spinner("Generating your ATS-optimized CV... This may take up to 30 seconds."):
                        result = api_client.generate_cv(job_description)
                    
                    st.success(f"✅ CV Generated! ATS Score: {result.get('ats_score', 0)}%")
                    
                    # Store result and navigate
                    st.session_state["selected_cv"] = result.get("_id")
                    st.session_state["current_page"] = "view_cv"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")


def show_view_cv_page():
    """Display CV view page with LaTeX preview and downloads."""
    cv_id = st.session_state.get("selected_cv")
    
    if not cv_id:
        st.warning("No CV selected")
        if st.button("Go to History"):
            st.session_state["current_page"] = "history"
            st.rerun()
        return
    
    try:
        cv = api_client.get_cv(cv_id)
    except Exception as e:
        st.error(f"Error loading CV: {str(e)}")
        return
    
    st.header("📄 Your Generated CV")
    
    # ATS Score display
    score = cv.get("ats_score", 0)
    score_class = "high" if score >= 90 else "medium" if score >= 70 else "low"
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f'<p class="ats-score ats-score-{score_class}">ATS Score: {score}%</p>', unsafe_allow_html=True)
    
    st.divider()
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📝 LaTeX Code", "📥 Download", "ℹ️ Details"])
    
    with tab1:
        st.subheader("LaTeX Source Code")
        st.info("You can copy and modify this LaTeX code as needed.")
        
        latex_code = cv.get("latex_code", "")
        st.code(latex_code, language="latex")
        
        st.download_button(
            label="📄 Download LaTeX (.tex)",
            data=latex_code,
            file_name="cv.tex",
            mime="text/plain",
            use_container_width=True
        )
    
    with tab2:
        st.subheader("Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**PDF Download**")
            st.write("Best for applications and printing")
            
            if st.button("📄 Download PDF", use_container_width=True, type="primary"):
                try:
                    with st.spinner("Compiling PDF..."):
                        pdf_content = api_client.download_pdf(cv_id)
                    
                    st.download_button(
                        label="💾 Save PDF",
                        data=pdf_content,
                        file_name="cv.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF generation failed: {str(e)}")
                    st.info("Tip: Make sure LaTeX (pdflatex/xelatex) is installed on the server.")
        
        with col2:
            st.write("**DOCX Download**")
            st.write("Editable in Microsoft Word")
            
            if st.button("📝 Download DOCX", use_container_width=True):
                try:
                    with st.spinner("Converting to DOCX..."):
                        docx_content = api_client.download_docx(cv_id)
                    
                    st.download_button(
                        label="💾 Save DOCX",
                        data=docx_content,
                        file_name="cv.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"DOCX conversion failed: {str(e)}")
                    st.info("Tip: Make sure Pandoc is installed on the server.")
    
    with tab3:
        st.subheader("CV Details")
        
        st.write(f"**Created:** {cv.get('created_at', '')[:19]}")
        st.write(f"**ATS Score:** {score}%")
        
        st.write("**Aligned Skills:**")
        skills = cv.get("aligned_skills", [])
        if skills:
            st.write(", ".join(skills))
        else:
            st.write("No specific skill alignment recorded")
        
        st.write("**Job Description:**")
        st.text_area("JD", value=cv.get("job_description", ""), height=200, disabled=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Back to History", use_container_width=True):
            st.session_state["current_page"] = "history"
            st.rerun()
    
    with col2:
        if st.button("🗑️ Delete this CV", use_container_width=True):
            try:
                api_client.delete_cv(cv_id)
                st.success("CV deleted!")
                st.session_state["current_page"] = "history"
                st.rerun()
            except Exception as e:
                st.error(str(e))


def show_history_page():
    """Display CV history page."""
    st.header("📜 CV Generation History")
    
    try:
        history = api_client.get_cv_history(limit=50)
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")
        return
    
    if not history:
        st.info("You haven't generated any CVs yet.")
        if st.button("Generate Your First CV", use_container_width=True):
            st.session_state["current_page"] = "generate"
            st.rerun()
        return
    
    for cv in history:
        score = cv.get("ats_score", 0)
        score_emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
        
        with st.expander(f"{score_emoji} ATS Score: {score}% | {cv.get('created_at', '')[:10]}"):
            st.write(f"**Job Description Preview:**")
            jd = cv.get("job_description", "")
            st.text(jd[:300] + "..." if len(jd) > 300 else jd)
            
            st.write(f"**Aligned Skills:** {', '.join(cv.get('aligned_skills', [])[:5])}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("👁️ View", key=f"view_{cv['_id']}"):
                    st.session_state["selected_cv"] = cv["_id"]
                    st.session_state["current_page"] = "view_cv"
                    st.rerun()
            
            with col2:
                if st.button("📄 Download PDF", key=f"pdf_{cv['_id']}"):
                    try:
                        with st.spinner("Generating PDF..."):
                            pdf_content = api_client.download_pdf(cv["_id"])
                        st.download_button(
                            label="💾 Save",
                            data=pdf_content,
                            file_name=f"cv_{cv['_id'][:8]}.pdf",
                            mime="application/pdf",
                            key=f"save_pdf_{cv['_id']}"
                        )
                    except Exception as e:
                        st.error(str(e))
            
            with col3:
                if st.button("🗑️ Delete", key=f"del_{cv['_id']}"):
                    try:
                        api_client.delete_cv(cv["_id"])
                        st.success("Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


def main():
    """Main application entry point."""
    # Check authentication
    if not api_client.is_authenticated():
        show_login_page()
        return
    
    # Show sidebar
    show_sidebar()
    
    # Get current page
    current_page = st.session_state.get("current_page", "dashboard")
    
    # Route to appropriate page
    if current_page == "dashboard":
        show_dashboard()
    elif current_page == "profile":
        show_profile_page()
    elif current_page == "generate":
        show_generate_cv_page()
    elif current_page == "history":
        show_history_page()
    elif current_page == "view_cv":
        show_view_cv_page()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
