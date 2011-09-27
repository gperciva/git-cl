#!/usr/bin/env python

import sys
import re
import os.path

# API docs:
#   http://code.google.com/p/support/wiki/IssueTrackerAPIPython
import gdata.projecthosting.client
import gdata.projecthosting.data
import gdata.gauth
import gdata.client
import gdata.data
import atom.http_core
import atom.core



class PatchBot():
    client = gdata.projecthosting.client.ProjectHostingClient()

    # you can use mewes for complete junk testing
    #PROJECT_NAME = "mewes"
    PROJECT_NAME = "lilypond"

    username = None
    password = None

    def __init__(self):
        # both of these bail if they fail
        self.get_credentials()
        self.login()

    def get_credentials(self):
        # TODO: can we use the coderview cookie for this?
        #filename = os.path.expanduser("~/.codereview_upload_cookies")
        filename = os.path.expanduser("~/.lilypond-project-hosting-login")
        try:
            login_data = open(filename).readlines()
            self.username = login_data[0]
            self.password = login_data[1]
        except:
            print "Could not find stored credentials"
            print "  %(filename)s" % locals()
            print "Please enter loging details manually"
            print
            import getpass
            print "Username (google account name):"
            self.username = raw_input().strip()
            self.password = getpass.getpass()

    def login(self):
        try:
            self.client.client_login(
                self.username, self.password,
                source='lilypond-patch-handler', service='code')
        except:
            print "Incorrect username or password"
            sys.exit(1)


    def create_issue(self, subject, description):
        """Create an issue."""
        return self.client.add_issue(
            self.PROJECT_NAME,
            "Patch: " + subject,
            description,
            self.username,
            labels = ["Type-Enhancement", "Patch-new"])

    def update_issue(self, issue_id, description):
        try:
            issue = self.client.update_issue(
                self.PROJECT_NAME,
                issue_id,
                self.username,
                comment = description,
                labels = ["Patch-new"])
        # TODO: this is a bit hack-ish, but I'm new to exceptions
        except gdata.client.RequestError as err:
            if err.body == "No permission to edit issue":
                issue = self.client.update_issue(
                    self.PROJECT_NAME,
                    issue_id,
                    self.username,
                    comment = description)
                return issue, "need to email -devel"
            else:
                issue = None, "need to email -devel"
        return issue, None

    def find_fix_issue_id(self, text):
        splittext = re.findall(r'\w+', text)
        issue_id = None
        # greedy search for the issue id
        for i, word in enumerate(splittext):
            if word in ["fix", "issue", "Fix", "Issue"]:
                try:
                    maybe_number = splittext[i+1]
                    if maybe_number[-1] == ")":
                        maybe_number = maybe_number[:-1]
                    issue_id = int(maybe_number)
                    break
                except:
                    pass
        if not issue_id:
            try:
                maybe_number = re.findall(r'\([0-9]+\)', text)
                issue_id = int(maybe_number[0][1:-1])
            except:
                pass
        return issue_id

    def upload(self, issue, patchset, subject="", description=""):
        if not subject:
            subject = "new patch"
        description = description + "\n\n" + "http://codereview.appspot.com/" + issue
        # update or create?
        issue_id = self.find_fix_issue_id(subject+' '+description)
        if issue_id:
            issue, problem = self.update_issue(issue_id, description)
            if problem == "need to email -devel":
                print "WARNING: could not change issue labels;"
                print "please email lilypond-devel with the issue",
                print "number: %i" % issue_id
        else:
            self.create_issue(subject, description)
        return True


# hacky integration
def upload(issue, patchset, subject="", description=""):
    patchy = PatchBot()
    status = patchy.upload(issue, patchset, subject, description)
    if status:
        print "Tracker issue done"
    else:
        print "Problem with the tracker issue"

def test_find_number():
    patchy = PatchBot()
    print patchy.find_fix_issue_id("Fix 123")
    print patchy.find_fix_issue_id("(Issue 123)")
    print patchy.find_fix_issue_id("(123)")

##test_find_number()
#upload("rietveld_issue_id", None, "test issue", "blah")
#upload("rietveld_issue_id", None, "test fix 1", "blah")

