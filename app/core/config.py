from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Admission Agent API"
    ENVIRONMENT: str = "local"
    
    # Database url (for the database hosted by neon)
    DATABASE_URL: str
    
    
    # api keys for the gemini llm
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.6-flash"


    # To create and validate jwt access tokens
    SECRET_KEY: str = "temporary_local_secret_key_12345!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


    # ---- FILEBASE OBJECT STORAGE CONFIGURATION ----
    FILEBASE_ACCESS_KEY: str
    FILEBASE_SECRET_KEY: str
    FILEBASE_BUCKET_NAME: str
    
    # Filebase uses a fixed, static S3 endpoint URL
    FILEBASE_ENDPOINT: str = "https://s3.filebase.io"

    # BREVO
    # ---- BREVO EMAIL CONFIGURATION ----
    BREVO_API_KEY: str
    SENDER_EMAIL: EmailStr
    SENDER_NAME: str

    PUBLIC_BASE_URL: str = "http://localhost:8001"

    # Instructs Pydantic to scan, locate, and read the local .env configuration file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

# Instantiate a global singleton settings object to be imported across your app modules
settings = Settings()


