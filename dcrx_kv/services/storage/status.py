from enum import Enum


class JobStatus(Enum):
    CREATING='CREATING'
    CREATED='CREATED'
    WRITING='WRITING'
    READING='READING'
    DELETING='DELETING'
    DONE='DONE'
    FAILED='FAILED'
    CANCELLED='CANCELLED'