from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    GREENHOUSE_SEARCH_QUERY: str
    GREENHOUSE_URL_TEMPLATE: str

    LEVER_SEARCH_QUERY: str
    LEVER_URL_TEMPLATE: str

    WORKABLE_SEARCH_QUERY: str = 'site:apply.workable.com "Software Engineer" india'
    WORKABLE_URL_TEMPLATE: str = (
        "https://apply.workable.com/api/v3/accounts/{company_code}/jobs"
    )

    ASHBY_SEARCH_QUERY: str = 'site:jobs.ashbyhq.com "Bangalore"'
    ASHBY_URL_TEMPLATE: str = (
        "https://api.ashbyhq.com/posting-api/job-board/{company_code}"
        "?includeCompensation=true"
    )

    SMARTRECRUITERS_SEARCH_QUERY: str = 'site:jobs.smartrecruiters.com "Bangalore"'
    SMARTRECRUITERS_URL_TEMPLATE: str = (
        "https://api.smartrecruiters.com/v1/companies/{company_code}/postings"
    )

    POST_URL: str

    JOBS_AUTH_KEY: str


settings = Settings()
