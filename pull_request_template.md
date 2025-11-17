## 📌 Summary
<!-- A brief description of the changes made in this PR and/or link(s) to any relevant Jira story and/or Service Now incident -->
- 

## 📣 Notes for Reviewers
<!-- Optional but encouraged: Any additional context or points of focus for reviewers. -->
- e.g. This PR introduces a change in `X`, so please verify `Y` to ensure that _______


## 🧪 How to Test
<!-- Include list of endpoints to test, Postman collection, or instructions on how to test this code submission. -->
e.g.
1. To test locally, checkout this branch: `git checkout BRANCH_NAME`
1. Run the application
1. Test the API via Postman
1. Test endpoints: `a`, `b`, `c`  


## 🏗 Feature Flagging (if applicable)
<!-- If this PR introduces a feature flag, provide details. -->
- **Feature Flag Name:** `FEATURE_FLAG_NAME`
- **Harness link:** Link to harness
- **Flag Removal Plan:** (When are we removing flag? What story accounts for code cleanup?) 


------------

#### ✅ Code Review/Merge Checklist

> [!NOTE]
> Objective of below checklist is to ensure reviewers and submitters focus on the **most critical areas** while keeping the review process **efficient and actionable**. 🚀  

As the author and/or as a code reviewer, please make sure you assess the following:

- [ ] Submitter is the assignee of this PR
- [ ] A review has been requested to our [Github Team](https://github.com/orgs/8451LLC/teams/maponsite3p)
- [ ] The Jira Story ID is included in either the title of this PR or there is a link to the story in the description

#### 📝 Code Quality & Maintainability
- [ ] Does this PR introduce any unnecessary complexity or tech debt?
- [ ] Could SOLID and/or DRY principles be better applied in this or a future code submission?
- [ ] Are there any potential performance bottlenecks or vulnerabilities being introduced?
- [ ] Is error handling properly implemented (e.g., retries, fallbacks)?
- [ ] Code follows the [style guideline](https://peps.python.org/pep-0008) and other established [engineering standards](https://confluence.kroger.com/confluence/display/8451KPMME/OP+-+02+-+Engineering+Standards#OP02EngineeringStandards-CodeStandardsandBestPractices) of the project? 
- [ ] Is [API spec properly updated](https://confluence.kroger.com/confluence/display/8451KPMME/OP+-+04+-+API+Spec+and+Documentation+Standards) and will be [uploaded](https://confluence.kroger.com/confluence/display/8451KPMME/KAP+API+-+Updating+OpenAPI+Spec+in+External+Catalog) to [https://developer.8451.com](https://developer.8451.com) ?
- [ ] If applicable: Has our [Confluence Engineering Space](https://confluence.kroger.com/confluence/display/8451KPMME/Engineering+Onsite+Partnership) been updated accordingly? (e.g. [upstream dependencies](https://confluence.kroger.com/confluence/display/8451KPMME/Upstream+Dependency+Matrix), [architecture diagrams](https://confluence.kroger.com/confluence/display/8451KPMME/PLA+API), [decision logs](https://confluence.kroger.com/confluence/display/8451KPMME/Kroger+Ad+Platform+API+-+Project+Decision+Log), etc.)  

#### 🧪 Testing & Validation
- [ ] Are there sufficient **unit tests integration tests, and regression tests**?
- [ ] Unit Tests are updated as needed, and code coverage is of **at least 80%**
- [ ] Are edge cases and failure scenarios accounted for?
- [ ] If applicable: Synthetic Tests have been updated? Or new synthetics have been created?
- [ ] All Acceptance Criteria (as defined by the corresponding User Story) is met
- [ ] All observations by reviewers have been properly addressed  