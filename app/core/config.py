from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Admission Agent API"
    ENVIRONMENT: str = "local"
    
    # This is the ONLY strictly required field for Phase 1/2
    DATABASE_URL: str
    
    # We provide fallback defaults for AI/Security keys so your app doesn't crash 
    # even if these variables are empty or missing in your .env file right now.
    GOOGLE_API_KEY: str = "placeholder_key_until_phase_4"
    GEMINI_MODEL: str = "gemini-3.6-flash"
    SECRET_KEY: str = "temporary_local_secret_key_12345!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


    # ---- FILEBASE OBJECT STORAGE CONFIGURATION ----
    # These will be read dynamically from your updated .env file
    FILEBASE_ACCESS_KEY: str
    FILEBASE_SECRET_KEY: str
    FILEBASE_BUCKET_NAME: str
    
    # Filebase uses a fixed, static S3 endpoint URL
    FILEBASE_ENDPOINT: str = "https://s3.filebase.io"

    # Instructs Pydantic to scan, locate, and read the local .env configuration file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

# Instantiate a global singleton settings object to be imported across your app modules
settings = Settings()


