def test_app_config_default_values(monkeypatch):
    for key in ['DATABASE_URL', 'RABBITMQ_URL', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 
                'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB']:
        monkeypatch.delenv(key, raising=False)
    
    from importlib import reload
    import app.core.config as app_config
    reload(app_config)
    
    settings = app_config.Settings()
    
    assert 'postgresql+asyncpg://' in settings.database_url
    assert 'amqp://' in settings.rabbitmq_url


def test_app_config_from_env(monkeypatch):
    custom_db_url = "postgresql+asyncpg://testuser:testpass@testhost:5432/testdb"
    custom_rabbitmq_url = "amqp://testuser:testpass@testhost:5672/"
    
    monkeypatch.setenv('DATABASE_URL', custom_db_url)
    monkeypatch.setenv('RABBITMQ_URL', custom_rabbitmq_url)
    
    from importlib import reload
    import app.core.config as app_config
    reload(app_config)
    
    settings = app_config.Settings()
    
    assert settings.database_url == custom_db_url
    assert settings.rabbitmq_url == custom_rabbitmq_url


def test_app_config_postgres_env_vars(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.setenv('POSTGRES_USER', 'myuser')
    monkeypatch.setenv('POSTGRES_PASSWORD', 'mypass')
    monkeypatch.setenv('POSTGRES_HOST', 'myhost')
    monkeypatch.setenv('POSTGRES_PORT', '5433')
    monkeypatch.setenv('POSTGRES_DB', 'mydb')
    
    from importlib import reload
    import app.core.config as app_config
    reload(app_config)
    
    settings = app_config.Settings()
    
    assert 'myuser' in settings.database_url
    assert 'mypass' in settings.database_url
    assert 'myhost' in settings.database_url
    assert '5433' in settings.database_url
    assert 'mydb' in settings.database_url


def test_consumer_config_default_values(monkeypatch):
    for key in ['DATABASE_URL', 'RABBITMQ_URL', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 
                'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB']:
        monkeypatch.delenv(key, raising=False)
    
    from importlib import reload
    import consumer.core.config as consumer_config
    reload(consumer_config)
    
    settings = consumer_config.Settings()
    
    assert 'postgresql+asyncpg://' in settings.database_url
    assert 'amqp://' in settings.rabbitmq_url


def test_consumer_config_from_env(monkeypatch):
    custom_db_url = "postgresql+asyncpg://consumer:consumerpass@dbhost:5432/consumerdb"
    custom_rabbitmq_url = "amqp://consumer:consumerpass@mqhost:5672/"
    
    monkeypatch.setenv('DATABASE_URL', custom_db_url)
    monkeypatch.setenv('RABBITMQ_URL', custom_rabbitmq_url)
    
    from importlib import reload
    import consumer.core.config as consumer_config
    reload(consumer_config)
    
    settings = consumer_config.Settings()
    
    assert settings.database_url == custom_db_url
    assert settings.rabbitmq_url == custom_rabbitmq_url


def test_config_database_url_priority(monkeypatch):
    explicit_db_url = "postgresql+asyncpg://explicit:explicit@explicit:5432/explicit"
    
    monkeypatch.setenv('DATABASE_URL', explicit_db_url)
    monkeypatch.setenv('POSTGRES_USER', 'ignored')
    monkeypatch.setenv('POSTGRES_PASSWORD', 'ignored')
    monkeypatch.setenv('POSTGRES_HOST', 'ignored')
    
    from importlib import reload
    import app.core.config as app_config
    reload(app_config)
    
    settings = app_config.Settings()
    
    assert settings.database_url == explicit_db_url
    assert 'ignored' not in settings.database_url

