import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def create_streamlit_app():
    st.set_page_config(
        page_title="AI Job Search Engine",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 AI-Powered Job Search Engine")
    st.markdown("Find your perfect job match using advanced BERT embeddings!")

    # Initialize the job matcher (you'll need to provide your Pinecone credentials)
    @st.cache_resource
    def load_job_matcher():
        return IntelligentJobMatcher(
            pinecone_api_key="your-pinecone-api-key",
            pinecone_env="your-pinecone-environment"
        )

    job_matcher = load_job_matcher()

    # Sidebar for search options
    st.sidebar.header("Search Options")
    search_type = st.sidebar.selectbox(
        "Search Type",
        ["Job Search", "Resume Matching", "Skill Gap Analysis"]
    )

    if search_type == "Job Search":
        st.header("🔍 Search Jobs")

        # Search input
        query = st.text_area(
            "Describe your ideal job or enter keywords:",
            placeholder="e.g., Senior Python Developer with machine learning experience"
        )

        # Filters
        col1, col2 = st.columns(2)
        with col1:
            experience_filter = st.selectbox(
                "Experience Level",
                ["Any", "Entry", "Mid", "Senior"]
            )

        with col2:
            num_results = st.slider("Number of Results", 5, 50, 10)

        if st.button("Search Jobs") and query:
            with st.spinner("Searching for relevant jobs..."):
                # Prepare filters
                filters = {}
                if experience_filter != "Any":
                    filters['experience_level'] = experience_filter.lower()

                # Search jobs
                results = job_matcher.search_jobs(
                    query=query,
                    filters=filters if filters else None,
                    top_k=num_results
                )

                # Display results
                st.subheader(f"Found {len(results)} matching jobs:")

                for i, result in enumerate(results):
                    metadata = result['metadata']
                    similarity_score = result['score']

                    with st.expander(
                            f"#{i + 1} {metadata['title']} at {metadata['company']} (Match: {similarity_score:.2%})"):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Company:** {metadata['company']}")
                            st.write(f"**Location:** {metadata['location']}")
                            st.write(f"**Experience Level:** {metadata['experience_level'].title()}")

                        with col2:
                            st.metric("Similarity Score", f"{similarity_score:.2%}")

                        if metadata['skills']:
                            st.write("**Required Skills:**")
                            skills_text = " • ".join(metadata['skills'])
                            st.write(skills_text)

    elif search_type == "Resume Matching":
        st.header("📄 Resume Job Matching")

        resume_text = st.text_area(
            "Paste your resume or describe your experience:",
            height=200,
            placeholder="Paste your resume content here..."
        )

        num_matches = st.slider("Number of Job Matches", 5, 20, 10)

        if st.button("Find Matching Jobs") and resume_text:
            with st.spinner("Analyzing your resume and finding matches..."):
                matches = job_matcher.match_resume_to_jobs(
                    resume_text=resume_text,
                    top_k=num_matches
                )

                st.subheader(f"Top {len(matches)} job matches for your profile:")

                # Create a visualization of match scores
                scores = [match['score'] for match in matches]
                titles = [match['metadata']['title'] for match in matches]

                fig = px.bar(
                    x=scores,
                    y=titles,
                    orientation='h',
                    title="Job Match Scores",
                    labels={'x': 'Similarity Score', 'y': 'Job Title'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                # Display detailed matches
                for i, match in enumerate(matches):
                    metadata = match['metadata']
                    score = match['score']

                    with st.expander(f"#{i + 1} {metadata['title']} (Match: {score:.2%})"):
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.write(f"**Company:** {metadata['company']}")
                            st.write(f"**Location:** {metadata['location']}")
                            if metadata['skills']:
                                st.write(f"**Skills:** {', '.join(metadata['skills'])}")

                        with col2:
                            st.metric("Match Score", f"{score:.2%}")

    elif search_type == "Skill Gap Analysis":
        st.header("📊 Skill Gap Analysis")

        col1, col2 = st.columns(2)

        with col1:
            resume_text = st.text_area(
                "Your Resume/Experience:",
                height=200,
                placeholder="Describe your skills and experience..."
            )

        with col2:
            target_job_id = st.text_input(
                "Target Job ID:",
                placeholder="Enter job ID from search results"
            )

        if st.button("Analyze Skill Gap") and resume_text and target_job_id:
            analyzer = SkillGapAnalyzer(job_matcher)

            with st.spinner("Analyzing skill gaps..."):
                analysis = analyzer.analyze_skill_gaps(resume_text, target_job_id)

                if "error" in analysis:
                    st.error(analysis["error"])
                else:
                    # Display match percentage
                    st.metric(
                        "Overall Match",
                        f"{analysis['match_percentage']}%",
                        delta=f"{analysis['match_percentage'] - 70:.1f}% vs average"
                    )

                    # Skills breakdown
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.subheader("✅ Matching Skills")
                        for skill in analysis['matching_skills']:
                            st.write(f"• {skill}")

                    with col2:
                        st.subheader("❌ Missing Skills")
                        for skill in analysis['missing_skills']:
                            st.write(f"• {skill}")

                    with col3:
                        st.subheader("➕ Extra Skills")
                        for skill in analysis['extra_skills']:
                            st.write(f"• {skill}")

                    # Recommendations
                    if analysis['recommendations']:
                        st.subheader("💡 Learning Recommendations")
                        for rec in analysis['recommendations']:
                            st.write(f"• {rec}")


if __name__ == "__main__":
    create_streamlit_app()
