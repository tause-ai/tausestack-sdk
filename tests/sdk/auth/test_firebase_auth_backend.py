import pytest
from unittest import mock
import firebase_admin
import time

from tausestack.sdk.auth.backends.firebase_admin import FirebaseAuthBackend
from tausestack.sdk.auth.base import User
from tausestack.sdk.auth.exceptions import (
    AuthException,
    InvalidTokenException,
    UserNotFoundException,
    AccountDisabledException,
)

# Mock para las credenciales de Firebase
@pytest.fixture
def mock_firebase_credentials():
    with mock.patch('firebase_admin.credentials.Certificate') as mock_cert:
        yield mock_cert

# Mock para la inicialización de la app de Firebase
@pytest.fixture
def mock_firebase_initialize_app():
    with mock.patch('firebase_admin.initialize_app') as mock_init_app, \
         mock.patch('firebase_admin.get_app') as mock_get_app:
        
        # Configurar mock_get_app para que inicialmente falle (simula que ninguna app existe)
        # Esto fuerza al constructor de FirebaseAuthBackend a llamar a initialize_app.
        mock_get_app.side_effect = ValueError("Simulated: Firebase app [DEFAULT] not found or other initial error.")

        # Configurar mock_init_app para que devuelva un objeto App mockeado cuando se llame
        mock_created_app = mock.MagicMock(spec=firebase_admin.App)
        # El nombre de la app creada por el backend será único, no '[DEFAULT]'
        # No necesitamos predecir el UUID aquí, solo asegurar que es un objeto App.
        mock_init_app.return_value = mock_created_app

        # Guardar el estado original de _default_app para restaurarlo después del test.
        # Esto es importante si las pruebas se ejecutan en un entorno donde _default_app podría
        # haber sido establecido por una prueba anterior o por una inicialización real.
        original_default_app_state = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None # Asegurar que está limpio antes de cada test de inicialización
        
        yield mock_init_app # La prueba usará esto para verificar si initialize_app fue llamado
        
        # Restaurar el estado original de _default_app
        FirebaseAuthBackend._default_app = original_default_app_state

# Mock para el módulo firebase_admin.auth
@pytest.fixture
def mock_config_sources():
    with mock.patch('tausestack.sdk.auth.backends.firebase_admin.os.getenv') as mock_getenv, \
         mock.patch('tausestack.sdk.auth.backends.firebase_admin.secrets.get') as mock_secrets_get:
        # Default behavior: no env vars or secrets found
        mock_getenv.return_value = None
        mock_secrets_get.return_value = None
        yield mock_getenv, mock_secrets_get

@pytest.fixture
def mock_firebase_auth_module():
    with mock.patch('tausestack.sdk.auth.backends.firebase_admin.auth') as mock_auth:
        # Define simple, local exception classes to avoid import and metaclass issues.
        # The backend only cares about the exception type's name, not its implementation.
        class AuthError(Exception):
            def __init__(self, message, cause=None, http_response=None):
                super().__init__(message)
                self.code = 'UNKNOWN_ERROR' # Default code
                self.cause = cause
                self.http_response = http_response

        class RevokedIdTokenError(AuthError): pass
        class UserDisabledError(AuthError): pass
        class InvalidIdTokenError(AuthError): pass
        class UserNotFoundError(AuthError): pass
        class EmailAlreadyExistsError(AuthError): pass
        class UidAlreadyExistsError(AuthError): pass

        # Assign the simple local classes to the mock
        mock_auth.AuthError = AuthError
        mock_auth.RevokedIdTokenError = RevokedIdTokenError
        mock_auth.UserDisabledError = UserDisabledError
        mock_auth.InvalidIdTokenError = InvalidIdTokenError
        mock_auth.UserNotFoundError = UserNotFoundError
        mock_auth.EmailAlreadyExistsError = EmailAlreadyExistsError
        mock_auth.UidAlreadyExistsError = UidAlreadyExistsError
        yield mock_auth

@pytest.fixture
def firebase_auth_backend(mock_firebase_credentials, mock_firebase_initialize_app):
    FirebaseAuthBackend._default_app = None 
    backend = FirebaseAuthBackend(service_account_key_dict={'type': 'service_account'})
    return backend

@pytest.fixture
def mock_user_record():
    """Fixture for a mocked Firebase UserRecord. Uses plain strings for data."""
    user = mock.MagicMock()
    user.uid = 'test_uid'
    user.email = 'test@example.com'
    user.display_name = 'Test User'
    user.phone_number = '+11234567890'
    user.photo_url = 'http://example.com/photo.png'
    user.disabled = False
    user.email_verified = True
    user.custom_claims = {'role': 'user'}
    
    # Add missing fields required by the Pydantic User model
    user.provider_id = 'firebase'
    user.tokens_valid_after_timestamp = int(time.time() * 1000)
    
    # Mock user_metadata
    metadata = mock.MagicMock()
    metadata.creation_timestamp = int(time.time() * 1000) - 10000
    metadata.last_sign_in_timestamp = int(time.time() * 1000)
    user.user_metadata = metadata
    
    # Mock provider_data
    provider_data_mock = mock.MagicMock()
    provider_data_mock.uid = 'provider_uid'
    provider_data_mock.email = 'provider_email@example.com'
    provider_data_mock.display_name = 'Provider Display Name'
    provider_data_mock.photo_url = 'http://example.com/provider_photo.png'
    provider_data_mock.provider_id = 'google.com'
    user.provider_data = [provider_data_mock]
    
    return user

class TestFirebaseAuthBackendInitialization:
    # Test case for direct dictionary credential
    def test_initialize_with_dict_success(self, mock_firebase_credentials, mock_firebase_initialize_app, mock_config_sources):
        FirebaseAuthBackend._default_app = None # Reset for each init test
        mock_getenv, mock_secrets_get = mock_config_sources
        
        cred_dict = {'type': 'service_account', 'project_id': 'test-project-dict'}
        backend = FirebaseAuthBackend(service_account_key_dict=cred_dict)
        
        mock_firebase_credentials.assert_called_once_with(cred_dict)
        mock_firebase_initialize_app.assert_called_once()
        assert backend._default_app is not None
        mock_getenv.assert_not_called() # Should not try env if dict is provided
        mock_secrets_get.assert_not_called() # Should not try secrets if dict is provided

    # Test case for direct path credential
    def test_initialize_with_path_success(self, mock_firebase_credentials, mock_firebase_initialize_app, mock_config_sources):
        FirebaseAuthBackend._default_app = None
        mock_getenv, mock_secrets_get = mock_config_sources
        
        cred_path = '/fake/path/to/serviceAccount.json'
        backend = FirebaseAuthBackend(service_account_key_path=cred_path)
        
        mock_firebase_credentials.assert_called_once_with(cred_path)
        mock_firebase_initialize_app.assert_called_once()
        assert backend._default_app is not None
        mock_getenv.assert_not_called()
        mock_secrets_get.assert_not_called()

    # Test case for environment variable path
    def test_initialize_with_env_path_success(self, mock_firebase_credentials, mock_firebase_initialize_app, mock_config_sources):
        FirebaseAuthBackend._default_app = None
        mock_getenv, mock_secrets_get = mock_config_sources
        
        env_cred_path = '/env/path/serviceAccount.json'
        mock_getenv.side_effect = lambda key: env_cred_path if key == "TAUSESTACK_FIREBASE_SA_KEY_PATH" else None
        
        backend = FirebaseAuthBackend()
        
        mock_getenv.assert_any_call("TAUSESTACK_FIREBASE_SA_KEY_PATH")
        mock_firebase_credentials.assert_called_once_with(env_cred_path)
        mock_firebase_initialize_app.assert_called_once()
        assert backend._default_app is not None
        mock_secrets_get.assert_not_called() # Should not try secrets if env path is found

    # Test case for secrets JSON string
    def test_initialize_with_secrets_json_success(self, mock_firebase_credentials, mock_firebase_initialize_app, mock_config_sources):
        FirebaseAuthBackend._default_app = None
        mock_getenv, mock_secrets_get = mock_config_sources
        
        secret_json_str = '{"type": "service_account", "project_id": "test-project-secret"}'
        secret_dict = {'type': 'service_account', 'project_id': 'test-project-secret'}
        mock_secrets_get.side_effect = lambda key: secret_json_str if key == "TAUSESTACK_FIREBASE_SA_KEY_JSON" else None
        
        backend = FirebaseAuthBackend()
        
        mock_getenv.assert_any_call("TAUSESTACK_FIREBASE_SA_KEY_PATH") # Will be called first
        mock_secrets_get.assert_called_once_with("TAUSESTACK_FIREBASE_SA_KEY_JSON")
        mock_firebase_credentials.assert_called_once_with(secret_dict)
        mock_firebase_initialize_app.assert_called_once()
        assert backend._default_app is not None

    # Test case for credential priority (direct path > env > secrets)
    def test_initialize_credential_priority(self, mock_firebase_credentials, mock_firebase_initialize_app, mock_config_sources):
        FirebaseAuthBackend._default_app = None
        mock_getenv, mock_secrets_get = mock_config_sources

        direct_path = '/direct/path.json'
        mock_getenv.return_value = '/env/path.json' # This should be ignored
        mock_secrets_get.return_value = '{"type":"secret"}' # This should be ignored

        backend = FirebaseAuthBackend(service_account_key_path=direct_path)
        mock_firebase_credentials.assert_called_once_with(direct_path)
        mock_getenv.assert_not_called()
        mock_secrets_get.assert_not_called()
        assert backend._default_app is not None

    # Test case for failure when no credentials are found
    def test_no_credentials_anywhere_raises_value_error(self, mock_config_sources):
        FirebaseAuthBackend._default_app = None # Ensure clean state
        mock_getenv, mock_secrets_get = mock_config_sources
        # Ensure mocks return None, indicating no credentials found
        mock_getenv.return_value = None
        mock_secrets_get.return_value = None
        
        with pytest.raises(ValueError, match="No se proporcionaron credenciales de Firebase."):
            FirebaseAuthBackend()
        mock_getenv.assert_any_call("TAUSESTACK_FIREBASE_SA_KEY_PATH")
        mock_secrets_get.assert_called_once_with("TAUSESTACK_FIREBASE_SA_KEY_JSON")

    # Test case for invalid JSON from secrets
    def test_initialize_with_invalid_secrets_json_raises_value_error(self, mock_config_sources):
        FirebaseAuthBackend._default_app = None
        mock_getenv, mock_secrets_get = mock_config_sources
        
        invalid_json_str = '{"type": "service_account", "project_id": "test-project-secret" # missing closing brace'
        mock_secrets_get.side_effect = lambda key: invalid_json_str if key == "TAUSESTACK_FIREBASE_SA_KEY_JSON" else None
        
        with pytest.raises(ValueError, match="Error al decodificar TAUSESTACK_FIREBASE_SA_KEY_JSON"):
            FirebaseAuthBackend()
        mock_secrets_get.assert_called_once_with("TAUSESTACK_FIREBASE_SA_KEY_JSON")

class TestFirebaseAuthBackendVerifyToken:
    @pytest.mark.asyncio
    async def test_verify_token_success(self, firebase_auth_backend, mock_firebase_auth_module):
        expected_decoded_token = {'uid': 'test_uid', 'email': 'test@example.com'}
        mock_firebase_auth_module.verify_id_token.return_value = expected_decoded_token
        
        decoded_token = await firebase_auth_backend.verify_token('valid_token')
        
        mock_firebase_auth_module.verify_id_token.assert_called_once_with(
            'valid_token', app=firebase_auth_backend._default_app, check_revoked=True
        )
        assert decoded_token == expected_decoded_token

    @pytest.mark.asyncio
    async def test_verify_token_revoked(self, firebase_auth_backend, mock_firebase_auth_module):
        mock_firebase_auth_module.verify_id_token.side_effect = mock_firebase_auth_module.RevokedIdTokenError("revoked")
        with pytest.raises(InvalidTokenException, match="El token de ID ha sido revocado."):
            await firebase_auth_backend.verify_token('revoked_token')

class TestFirebaseAuthBackendGetUserFromToken:
    @pytest.mark.asyncio
    async def test_get_user_from_token_success(self, firebase_auth_backend, mock_firebase_auth_module, mock_user_record):
        verified_token = {'uid': 'test_uid'}
        mock_firebase_auth_module.get_user.return_value = mock_user_record

        user = await firebase_auth_backend.get_user_from_token(verified_token)

        mock_firebase_auth_module.get_user.assert_called_once_with('test_uid', app=firebase_auth_backend._default_app)
        assert isinstance(user, User)
        assert user.id == 'test_uid'
        assert user.email == 'test@example.com'

    @pytest.mark.asyncio
    async def test_get_user_from_token_no_uid(self, firebase_auth_backend):
        with pytest.raises(InvalidTokenException, match="Token verificado no contiene UID."):
            await firebase_auth_backend.get_user_from_token({'email': 'test@example.com'})

class TestFirebaseAuthBackendGetUserById:
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, firebase_auth_backend, mock_firebase_auth_module, mock_user_record):
        mock_firebase_auth_module.get_user.return_value = mock_user_record
        
        user = await firebase_auth_backend.get_user_by_id('test_uid')
        
        mock_firebase_auth_module.get_user.assert_called_once_with('test_uid', app=firebase_auth_backend._default_app)
        assert user.id == 'test_uid'
        assert str(user.photo_url) == 'http://example.com/photo.png'

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, firebase_auth_backend, mock_firebase_auth_module):
        mock_firebase_auth_module.get_user.side_effect = mock_firebase_auth_module.UserNotFoundError('not found')
        user = await firebase_auth_backend.get_user_by_id('unknown_uid')
        assert user is None

class TestFirebaseAuthBackendGetUserByEmail:
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, firebase_auth_backend, mock_firebase_auth_module, mock_user_record):
        test_email = 'test@example.com' # Use plain string
        mock_firebase_auth_module.get_user_by_email.return_value = mock_user_record
        
        user = await firebase_auth_backend.get_user_by_email(test_email)
        
        mock_firebase_auth_module.get_user_by_email.assert_called_once_with(test_email, app=firebase_auth_backend._default_app)
        assert user.email == test_email

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, firebase_auth_backend, mock_firebase_auth_module):
        test_email = 'unknown@example.com'
        mock_firebase_auth_module.get_user_by_email.side_effect = mock_firebase_auth_module.UserNotFoundError('not found')
        user = await firebase_auth_backend.get_user_by_email(test_email)
        assert user is None

class TestFirebaseAuthBackendCreateUser:
    @pytest.mark.asyncio
    async def test_create_user_all_params_success(self, firebase_auth_backend, mock_firebase_auth_module, mock_user_record):
        mock_firebase_auth_module.create_user.return_value = mock_user_record
        
        created_user = await firebase_auth_backend.create_user(
            email='new@example.com',
            password='newPassword123',
            uid='new_uid',
            display_name='New User',
            photo_url='http://example.com/new_photo.png',
            email_verified=True,
            disabled=False,
            phone_number='+11234567890'
        )
        
        mock_firebase_auth_module.create_user.assert_called_once()
        assert created_user.id == mock_user_record.uid

    @pytest.mark.asyncio
    async def test_create_user_email_already_exists(self, firebase_auth_backend, mock_firebase_auth_module):
        mock_firebase_auth_module.create_user.side_effect = mock_firebase_auth_module.EmailAlreadyExistsError('exists')
        with pytest.raises(AuthException, match="Error al crear usuario en Firebase"):
            await firebase_auth_backend.create_user(email='existing@example.com', password='password')

class TestFirebaseAuthBackendUpdateUser:
    @pytest.mark.asyncio
    async def test_update_user_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        # Preparamos el mock_user_record para que refleje los datos actualizados
        mock_user_record.email = 'updated@example.com'
        mock_user_record.display_name = 'Updated User'
        mock_user_record.disabled = True
        mock_firebase_auth_module.update_user.return_value = mock_user_record

        updated_user = await firebase_auth_backend.update_user(
            user_id='test_uid',
            email='updated@example.com',
            display_name='Updated User',
            photo_url='http://example.com/updated_photo.png',
            email_verified=False,
            disabled=True,
            password='newPassword456',
            phone_number='+19876543210'
        )

        mock_firebase_auth_module.update_user.assert_called_once_with(
            'test_uid',
            email='updated@example.com',
            display_name='Updated User',
            photo_url='http://example.com/updated_photo.png',
            email_verified=False,
            disabled=True,
            password='newPassword456',
            phone_number='+19876543210',
            app=firebase_auth_backend._default_app
        )
        assert updated_user is not None
        assert updated_user.id == 'test_uid'
        assert updated_user.email == 'updated@example.com'
        assert updated_user.display_name == 'Updated User'
        assert updated_user.disabled is True

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.update_user.side_effect = mock_firebase_auth_module.UserNotFoundError("User not found")
        
        with pytest.raises(UserNotFoundException, match="Usuario no encontrado para actualizar."):
            await firebase_auth_backend.update_user(user_id='user_to_update_not_found', display_name='New Name')

    @pytest.mark.asyncio
    async def test_update_user_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        mock_firebase_auth_module.update_user.side_effect = mock_firebase_auth_module.AuthError('Error genérico de Firebase.')
        
        with pytest.raises(AuthException, match="Error al actualizar usuario en Firebase: Error genérico de Firebase."):
            await firebase_auth_backend.update_user(user_id='test_uid', display_name='Updated Name', photo_url='http://example.com/new.png')

    @pytest.mark.asyncio
    async def test_update_user_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.update_user(user_id='any_user_sdk_init', display_name='Any Name') 
        finally:
            FirebaseAuthBackend._default_app = original_app



    @pytest.mark.asyncio
    async def test_update_user_single_field(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        # Mock UserRecord to reflect the upcoming change
        mock_user_record.display_name = 'Only Name Updated'
        mock_firebase_auth_module.update_user.return_value = mock_user_record

        updated_user = await firebase_auth_backend.update_user(
            user_id='test_uid_single',
            display_name='Only Name Updated'
        )

        mock_firebase_auth_module.update_user.assert_called_once_with(
            'test_uid_single',
            display_name='Only Name Updated',
            app=firebase_auth_backend._default_app
        )
        assert updated_user is not None
        assert updated_user.display_name == 'Only Name Updated'
        # Ensure other fields from mock_user_record are still there if they were part of the original mock
        assert updated_user.email == mock_user_record.email 

    @pytest.mark.asyncio
    async def test_update_user_clear_field(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        # Mock UserRecord to reflect the upcoming change
        mock_user_record.phone_number = ''
        mock_firebase_auth_module.update_user.return_value = mock_user_record

        updated_user = await firebase_auth_backend.update_user(
            user_id='test_uid_clear',
            phone_number=''
        )

        mock_firebase_auth_module.update_user.assert_called_once_with(
            'test_uid_clear',
            phone_number='',
            app=firebase_auth_backend._default_app
        )
        assert updated_user is not None
        assert updated_user.phone_number == ''

    @pytest.mark.asyncio
    async def test_update_user_field_as_none_no_change_in_payload(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        # If a field is passed as None, it should NOT be part of the payload to Firebase
        # The mock_user_record will be returned as is by the mocked update_user
        original_display_name = mock_user_record.display_name
        mock_firebase_auth_module.update_user.return_value = mock_user_record

        updated_user = await firebase_auth_backend.update_user(
            user_id='test_uid_none',
            display_name=None, # This should be filtered out
            email_verified=True # Include another valid field to ensure payload is not empty
        )
        
        # display_name=None should not be in the call to firebase_admin.auth.update_user
        # We expect only uid, email_verified, and app in the call
        # Need to capture arguments to check this properly
        args, kwargs = mock_firebase_auth_module.update_user.call_args
        assert args[0] == 'test_uid_none'
        assert 'display_name' not in kwargs
        assert kwargs['email_verified'] is True
        assert kwargs['app'] == firebase_auth_backend._default_app
        
        assert updated_user is not None
        # The display_name on the returned user should be the original one, as it wasn't updated
        assert updated_user.display_name == original_display_name
        # The email_verified status on mock_user_record might not be True by default, 
        # so we check what was actually passed and returned for that field.
        # For this test, we assume mock_user_record.email_verified is updated by the mocked call if it was in payload.
        # Let's ensure mock_user_record reflects the change for email_verified for assertion consistency.
        mock_user_record.email_verified = True 
        assert updated_user.email_verified is True

    @pytest.mark.asyncio
    async def test_update_user_with_extra_kwargs(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module, mock_user_record):
        mock_firebase_auth_module.update_user.return_value = mock_user_record

        await firebase_auth_backend.update_user(
            user_id='test_uid_extra',
            display_name='Extra Kwargs User',
            custom_unrecognized_kwarg='test_value' 
        )

        mock_firebase_auth_module.update_user.assert_called_once_with(
            'test_uid_extra',
            display_name='Extra Kwargs User',
            custom_unrecognized_kwarg='test_value',
            app=firebase_auth_backend._default_app
        )


class TestFirebaseAuthBackendDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_user_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_to_delete = 'user_to_delete_uid'
        mock_firebase_auth_module.delete_user.return_value = None 

        await firebase_auth_backend.delete_user(uid_to_delete)

        mock_firebase_auth_module.delete_user.assert_called_once_with(
            uid_to_delete,
            app=firebase_auth_backend._default_app
        )

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_not_found = 'unknown_uid'
        mock_firebase_auth_module.delete_user.side_effect = mock_firebase_auth_module.UserNotFoundError("Generic delete error")
        
        with pytest.raises(UserNotFoundException, match=f"Usuario con UID {uid_not_found} no encontrado al intentar eliminar."):
            await firebase_auth_backend.delete_user(uid_not_found)

    @pytest.mark.asyncio
    async def test_delete_user_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_error = 'error_uid'
        mock_firebase_auth_module.delete_user.side_effect = mock_firebase_auth_module.AuthError('Error genérico de Firebase al eliminar.')
        
        with pytest.raises(AuthException, match="Error al eliminar usuario en Firebase: Error genérico de Firebase al eliminar."):
            await firebase_auth_backend.delete_user(uid_error)

    @pytest.mark.asyncio
    async def test_delete_user_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.delete_user('any_uid')
        finally:
            FirebaseAuthBackend._default_app = original_app



class TestFirebaseAuthBackendSetCustomClaims:
    @pytest.mark.asyncio
    async def test_set_custom_claims_success(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid = 'test_uid_for_claims'
        claims = {'role': 'admin', 'premium': True}
        mock_firebase_auth_module.set_custom_user_claims.return_value = None

        await firebase_auth_backend.set_custom_user_claims(uid, claims)

        mock_firebase_auth_module.set_custom_user_claims.assert_called_once_with(
            uid,
            claims,
            app=firebase_auth_backend._default_app
        )

    @pytest.mark.asyncio
    async def test_set_custom_claims_user_not_found(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_not_found = 'non_existent_uid'
        claims = {'role': 'admin'}
        mock_firebase_auth_module.set_custom_user_claims.side_effect = mock_firebase_auth_module.UserNotFoundError("User not found")
        
        with pytest.raises(UserNotFoundException, match="Usuario no encontrado para establecer claims."):
            await firebase_auth_backend.set_custom_user_claims(uid_not_found, claims)

    @pytest.mark.asyncio
    async def test_set_custom_claims_generic_firebase_error(self, firebase_auth_backend: FirebaseAuthBackend, mock_firebase_auth_module):
        uid_error = 'error_uid_for_claims'
        claims = {'role': 'guest'}
        mock_firebase_auth_module.set_custom_user_claims.side_effect = mock_firebase_auth_module.AuthError("Generic claims error")
        
        with pytest.raises(AuthException, match=f"Error al establecer custom claims para el usuario {uid_error} en Firebase: Generic claims error"):
            await firebase_auth_backend.set_custom_user_claims(uid_error, claims)

    @pytest.mark.asyncio
    async def test_set_custom_claims_sdk_not_initialized(self, firebase_auth_backend: FirebaseAuthBackend):
        original_app = FirebaseAuthBackend._default_app
        FirebaseAuthBackend._default_app = None
        try:
            with pytest.raises(AuthException, match="Firebase Admin SDK no inicializado."):
                await firebase_auth_backend.set_custom_user_claims('any_uid_for_claims', {'role': 'any'}) 
        finally:
            FirebaseAuthBackend._default_app = original_app

# Fin de las clases de prueba para FirebaseAuthBackend
