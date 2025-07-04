import gitlab
import os
import asyncio
import json

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool

class GitlabHandler(BaseHandler):
    def __init__(self, private_token=None, url="https://gitlab.com"):
        self.token = private_token or os.getenv("GITLAB_PRIVATE_TOKEN")
        if not self.token:
            raise ValueError("No GitLab private token provided or set in GITLAB_PRIVATE_TOKEN.")

        self.gl = gitlab.Gitlab(url, private_token=self.token)
        self.gl.auth()
        print("✅ Connected to GitLab as:", self.gl.user.username)

    @tool
    async def get_user_profile(self):
        """
        Collects the GitLab user profile, including admin status, 2FA status, and basic metadata.
        Use this to retrieve current user's identity and security posture.
        """
        user = self.gl.user  # Basic current user info
        full_user = self.gl.users.get(user.id)  # Get full user object

        return {
            "id": full_user.id,
            "username": full_user.username,
            "name": full_user.name,
            "email": getattr(full_user, "email", None),
            "is_admin": getattr(full_user, "is_admin", False),
            "two_factor_enabled": getattr(full_user, "two_factor_enabled", None),
            "state": full_user.state,
            "created_at": full_user.created_at,
            "web_url": full_user.web_url
        }

    @tool
    async def get_projects(self):
        """
        Retrieves a list of all GitLab projects owned by the user.
        Includes visibility, default branch, and last activity.
        """
        projects_info = []
        for project in self.gl.projects.list(owned=True, all=True):
            project_info = {
                "id": project.id,
                "name": project.name,
                "visibility": project.visibility,
                "default_branch": project.default_branch,
                "last_activity_at": project.last_activity_at,
            }
            projects_info.append(project_info)
        return projects_info

    @tool
    async def get_groups_and_members(self):
        """
        Lists GitLab groups owned by the user and their members.
        Includes usernames, emails, and access levels.
        """
        groups_info = []
        for group in self.gl.groups.list(owned=True, all=True):
            members = [
                {
                    "username": m.username,
                    "access_level": m.access_level,
                    "email": m.email if hasattr(m, "email") else None,
                }
                for m in group.members.list()
            ]
            groups_info.append({
                "group_name": group.name,
                "group_id": group.id,
                "members": members,
            })
        return groups_info

    @tool
    async def get_issues(self):
        """
        Retrieves all GitLab issues assigned to the current user.
        Includes title, state, creation time, and labels.
        """
        all_issues = []
        for issue in self.gl.issues.list(scope='assigned-to-me', all=True):
            all_issues.append({
                "title": issue.title,
                "state": issue.state,
                "created_at": issue.created_at,
                "labels": issue.labels,
            })
        return all_issues

    @tool
    async def get_merge_requests(self):
        """
        Collects all merge requests assigned to the current user.
        Includes title, source/target branches, and state.
        """
        mrs = []
        for mr in self.gl.mergerequests.list(scope='assigned_to_me', all=True):
            mrs.append({
                "title": mr.title,
                "state": mr.state,
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch,
            })
        return mrs

    @tool
    async def get_hooks(self, project_id):
        """
        Fetches all webhooks configured for the specified GitLab project.
        """
        try:
            project = self.gl.projects.get(project_id)
            return [hook.attributes for hook in project.hooks.list()]
        except gitlab.exceptions.GitlabGetError:
            return []

    @tool
    async def get_pipelines(self, project_id):
        """
        Retrieves recent pipeline runs for a specific GitLab project.
        Includes status, ref, and timestamps.
        """
        try:
            project = self.gl.projects.get(project_id)
            return [
                {
                    "id": pipeline.id,
                    "status": pipeline.status,
                    "ref": pipeline.ref,
                    "updated_at": pipeline.updated_at,
                }
                for pipeline in project.pipelines.list()
            ]
        except gitlab.exceptions.GitlabGetError:
            return []

    @tool
    async def collect_all_gitlab_data(self):
        """
        Collects full GitLab profile data: user info, projects, groups, issues, and merge requests.
        Useful for complete audit or snapshot.
        """
        return {
            "user_profile": self.get_user_profile(),
            "projects": self.get_projects(),
            "groups": self.get_groups_and_members(),
            "issues": self.get_issues(),
            "merge_requests": self.get_merge_requests(),
        }
