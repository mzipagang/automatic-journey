# RBAC with JWTs
### Glossary
- JWT - Json Web Token
  - A digitally signed message that used to transmit information.
    - In our case, we use it to get information about a logged in client for authorization
- RBAC - Role-Based Access Control
  - In our example in this template, we use the Azure Groups the user is part of to authorize them to access certain endpoints
### This template's example
This template utilizes FastAPI Security to provide an example of using the JWT 'group' claim to authorize a user to use certain endpoints. Below is a brief walkthrough in how this is done.

1. Before continuing, make sure you have an optional ***Security Groups "groups"*** claim enabled in your Azure App Registration Token Configuration. This is a requirement for using this example.
2. Make sure you have up-to-date versions of the following pip dependencies: `python-jose` and `pydantic`.
3. In [utils/jwt.py](../app/common/utils/jwt.py), we include a method to extract a [User](../app/v2/model/user.py) object from the JWT:  
  ```py
  async def get_current_user(token: str = Depends(oauth2_scheme)):
      credentials_exception = HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Could not validate credentials",
          headers={"WWW-Authenticate": "Bearer"},
      )
      try:
          payload = jwt.get_unverified_claims(token)
          email: str = payload.get("unique_name")
          if email is None:
              raise credentials_exception
          user = User(email=email,
                      name=payload.get("name"),
                      groups=payload.get("groups"))
      except JWTError:
          raise credentials_exception
      return user
  ```
- From this User, we can perform role checks on certain groups: 
```py
  class RoleChecker:
    def __init__(self, allowed_groups: List):
        self.allowed_groups = allowed_groups

    def __call__(self, user: User = Depends(get_current_user)):
        has_perms = False
        for group in self.allowed_groups:
            if group in user.groups:
                has_perms = True
        if not has_perms:
            logger.debug(f"User {user.name} not in allowed groups {self.allowed_groups}")
            raise HTTPException(status_code=403, detail="Operation not permitted")
  ```
4. Let's re-define some groups which exist in Azure Active Directory. Over in [models/groups.py](../app/model/groups.py):
 ```py
  from enum import StrEnum
  # Place any groups you would like to use into this Enum along with the group id
  class Group(StrEnum):
      gAZArchApirefarchSuprt = "4a20c019-98b6-4d05-a317-974e793d16eb"
      failedGroup = "00000000-0000-0000-0000-000000000000"
   ```
- Note: These IDs are coming from Azure Active Directory. You can find them easily when looking at a group's overview page like [HERE](https://portal.azure.com/#view/Microsoft_AAD_IAM/GroupDetailsMenuBlade/~/Properties/groupId/4a20c019-98b6-4d05-a317-974e793d16eb).

5. Last but not least, let's secure some endpoints! The first will check if you belong to the above support group (your group will vary). And the second is a test endpoint which always fails (due to a dummy group ID, of which no-one has the right role). Over in [endpoints/secured.py](../app/v1/api/endpoints/secured.py):
```py
  # Demonstrates creating a permission, and then requiring said permission to use endpoint
  example_permission = RoleChecker([Group.gAZArchApirefarchSuprt])

  @router.get('/secured',
              name="Secured Endpoint",
              description="An example secured endpoint.",
              dependencies=[Depends(example_permission)],
              status_code=status.HTTP_200_OK)
  async def secured_endpoint(request: Request):
      return f"You just accessed a secured endpoint with permissions {example_permission.allowed_groups}."


  # RoleChecker can also be placed inline
  @router.get('/secured/inline',
              name="Secured Endpoint (Fail)",
              description="An endpoint that demonstrates inline permissions. As it uses a non-existent group, "
                          "no-one can access it.",
              dependencies=[Depends(RoleChecker([Group.failedGroup]))],
              status_code=status.HTTP_401_UNAUTHORIZED)
  async def secured_endpoint_inline(request: Request):
      return f"You didn't just access a secured endpoint with permissions {Group.failedGroup}."
      
  ```
- We do role checking by using FastAPI's [Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/), having our endpoints depend on the RoleChecker class.

### Additional Documentation
- [Official FastAPI Security Page](https://fastapi.tiangolo.com/tutorial/security/)
- [MS Docs on including group claims](https://docs.microsoft.com/en-us/azure/active-directory/hybrid/how-to-connect-fed-group-claims)
