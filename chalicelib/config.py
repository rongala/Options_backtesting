import os
from configparser import ConfigParser
from typing import Optional
from chalicelib.setup_logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages configuration from environment variables and config.ini file."""

    def __init__(self):
        self._config = None
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from config.ini file."""
        config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
        self._config = ConfigParser()
        if os.path.exists(config_file):
            self._config.read(config_file)
            logger.debug(f"Configuration loaded from {config_file}")

    def get_rds_connection_string(self, api_stage: str) -> str:
        """
        Get RDS connection string from environment variables or config file.

        @param api_stage: Stage name (LOCAL, DEV, PROD)
        @return: RDS connection string
        """
        # Try environment variables first (more secure)
        rds_host = os.getenv('RDS_HOST') or self._get_config_value(api_stage, 'RDS_HOST')
        rds_username = os.getenv('RDS_USERNAME') or self._get_config_value(api_stage, 'RDS_USERNAME')
        rds_password = os.getenv('RDS_USER_PWD') or self._get_config_value(api_stage, 'RDS_USER_PWD')
        rds_db_name = os.getenv('RDS_DB_NAME') or self._get_config_value(api_stage, 'RDS_DB_NAME')

        required_values = {
            'RDS_HOST': rds_host,
            'RDS_USERNAME': rds_username,
            'RDS_USER_PWD': rds_password,
            'RDS_DB_NAME': rds_db_name
        }

        missing = [k for k, v in required_values.items() if not v]
        if missing:
            raise ValueError(f"Missing RDS configuration: {', '.join(missing)}")

        conn_string = f"host={rds_host} user={rds_username} password={rds_password} dbname={rds_db_name}"
        logger.debug(f"RDS Connection String: host={rds_host} user={rds_username} dbname={rds_db_name}")
        return conn_string

    def get_ssh_config(self) -> dict:
        """
        Get SSH tunnel configuration from environment variables or config file.

        @return: SSH configuration dictionary
        """
        ssh_host = os.getenv('SSH_HOST') or self._get_config_value('local', 'SSH_HOST', 
                                                                      'ec2-54-190-122-132.us-west-2.compute.amazonaws.com')
        ssh_username = os.getenv('SSH_USERNAME') or self._get_config_value('local', 'SSH_USERNAME', 'ec2-user')
        ssh_key_path = os.getenv('SSH_PRIVATE_KEY')
        
        if not ssh_key_path:
            ssh_key_path = self._get_config_value('local', 'SSH_PRIV_KEY')
        
        remote_bind_address = os.getenv('REMOTE_BIND_ADDRESS') or self._get_config_value('local', 'REMOTE_BIND_ADDRESS',
                                                                                            'backtesting-db-east-cluster.cluster-ciaexrx2rcxr.us-east-1.rds.amazonaws.com')
        remote_bind_port = int(os.getenv('REMOTE_BIND_PORT', 5432))
        
        local_bind_address = os.getenv('LOCAL_BIND_ADDRESS') or self._get_config_value('local', 'LOCAL_BIND_ADDRESS', 'localhost')
        local_bind_port = int(os.getenv('LOCAL_BIND_PORT', 6543))

        if not ssh_key_path:
            raise ValueError("SSH_PRIVATE_KEY must be set via environment variable or config file")

        return {
            'ssh_host': ssh_host,
            'ssh_username': ssh_username,
            'ssh_key_path': ssh_key_path,
            'remote_bind_address': remote_bind_address,
            'remote_bind_port': remote_bind_port,
            'local_bind_address': local_bind_address,
            'local_bind_port': local_bind_port,
        }

    def get_ssh_db_credentials(self) -> dict:
        """
        Get SSH database credentials from environment variables or config file.

        @return: SSH database credentials dictionary
        """
        db_name = os.getenv('SSH_DB_NAME') or self._get_config_value('local', 'RDS_DB_NAME', 'GKBackTesting2')
        db_user = os.getenv('SSH_DB_USER') or self._get_config_value('local', 'RDS_USERNAME', 'postgres')
        db_password = os.getenv('SSH_DB_PASSWORD') or self._get_config_value('local', 'RDS_USER_PWD')

        if not db_password:
            raise ValueError("SSH_DB_PASSWORD must be set via environment variable or config file")

        return {
            'database': db_name,
            'user': db_user,
            'password': db_password,
        }

    def _get_config_value(self, section: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get configuration value from config file.

        @param section: Configuration section
        @param key: Configuration key
        @param default: Default value if key not found
        @return: Configuration value or default
        """
        if self._config and self._config.has_option(section, key):
            return self._config.get(section, key)
        return default


# Global config manager instance
config_manager = ConfigManager()
