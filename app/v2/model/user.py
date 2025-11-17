from pydantic import BaseModel, Field


class User(BaseModel):
    firstName: str = Field(
        default="", title="firstName", description="The first name of the user."
    )
    lastName: str = Field(
        default="", title="lastName", description="The last name of the user."
    )
    email: str = Field(default="", title="email", description="The email of the user.")
    organization: str = Field(
        default="", title="organization", description="The organization of the user."
    )
