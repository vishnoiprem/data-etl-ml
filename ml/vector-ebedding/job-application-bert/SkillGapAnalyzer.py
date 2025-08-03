class SkillGapAnalyzer:
    def __init__(self, job_matcher: IntelligentJobMatcher):
        self.job_matcher = job_matcher

    def analyze_skill_gaps(self, resume_text: str, target_job_id: str) -> Dict:
        """
        Analyze skill gaps between resume and target job
        """
        # Extract skills from resume
        resume_features = self.job_matcher.search_engine.extract_job_features(resume_text)
        resume_skills = set(resume_features['skills'])

        # Get target job details
        job_results = self.job_matcher.vector_db.index.fetch(ids=[target_job_id])

        if target_job_id not in job_results['vectors']:
            return {"error": "Job not found"}

        job_metadata = job_results['vectors'][target_job_id]['metadata']
        required_skills = set(job_metadata.get('skills', []))

        # Calculate gaps and matches
        matching_skills = resume_skills.intersection(required_skills)
        missing_skills = required_skills - resume_skills
        extra_skills = resume_skills - required_skills

        # Calculate match percentage
        if required_skills:
            match_percentage = len(matching_skills) / len(required_skills) * 100
        else:
            match_percentage = 0

        return {
            'match_percentage': round(match_percentage, 2),
            'matching_skills': list(matching_skills),
            'missing_skills': list(missing_skills),
            'extra_skills': list(extra_skills),
            'recommendations': self._generate_recommendations(missing_skills)
        }

    def _generate_recommendations(self, missing_skills: List[str]) -> List[str]:
        """
        Generate learning recommendations for missing skills
        """
        skill_resources = {
            'python': 'Consider taking Python courses on Coursera or practicing on LeetCode',
            'machine learning': 'Start with Andrew Ng\'s ML course and practice on Kaggle',
            'aws': 'Get AWS Cloud Practitioner certification',
            'docker': 'Practice containerization with Docker tutorials',
            'react': 'Build projects using React and deploy them on GitHub Pages'
        }

        recommendations = []
        for skill in missing_skills:
            if skill in skill_resources:
                recommendations.append(f"{skill.title()}: {skill_resources[skill]}")
            else:
                recommendations.append(f"{skill.title()}: Look for online courses and hands-on projects")

        return recommendations
