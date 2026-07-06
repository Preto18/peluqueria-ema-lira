import pytest
from app import app, db, User, Cliente, Cita, Pago, Gasto, Producto, Service, PROMO, limiter
from datetime import date, time, datetime
from werkzeug.security import generate_password_hash
from unittest.mock import patch


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['RATELIMIT_ENABLED'] = False  # Disable rate limiting for tests
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create admin user only if not exists
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', password_hash=generate_password_hash('admin123'))
                db.session.add(admin)
                db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()


@pytest.fixture
def logged_in_client(client):
    with patch.object(limiter, 'enabled', False):
        client.post('/admin/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
    return client


class TestAuth:
    def test_login_success(self, client):
        response = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Iniciaste sesi' in response.data

    def test_login_fail(self, client):
        response = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'wrong'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'incorrectos' in response.data

    def test_logout(self, logged_in_client):
        response = logged_in_client.get('/admin/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Cerraste sesi' in response.data


class TestPublicBooking:
    def test_landing_page(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Ema Lira' in response.data

    def test_agendar_page(self, client):
        response = client.get('/agendar')
        assert response.status_code == 200
        assert b'Confirmar Turno' in response.data

    def test_api_horarios(self, client):
        response = client.get('/api/horarios?fecha=2026-07-08')  # Miércoles
        assert response.status_code == 200
        data = response.get_json()
        assert 'horarios' in data
        assert len(data['horarios']) > 0


class TestAdminDashboard:
    def test_dashboard_requires_login(self, client):
        response = client.get('/admin', follow_redirects=True)
        assert response.status_code == 200
        assert b'Inici' in response.data  # Redirected to login

    def test_dashboard_access(self, logged_in_client):
        response = logged_in_client.get('/admin')
        assert response.status_code == 200
        assert b'Dashboard' in response.data


class TestClientes:
    def test_create_cliente(self, logged_in_client):
        response = logged_in_client.post('/admin/clientes/nuevo', data={
            'nombre': 'Test Cliente',
            'telefono': '1123456789',
            'email': 'test@test.com',
            'notas': 'Nota test'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'registrado correctamente' in response.data

    def test_list_clientes(self, logged_in_client):
        response = logged_in_client.get('/admin/clientes')
        assert response.status_code == 200
        assert b'Clientes' in response.data


class TestCitas:
    def test_create_cita(self, logged_in_client):
        # First create a cliente
        logged_in_client.post('/admin/clientes/nuevo', data={
            'nombre': 'Cliente Cita',
            'telefono': '1199999999',
        }, follow_redirects=True)
        
        response = logged_in_client.post('/admin/citas/nuevo', data={
            'cliente_id': '1',
            'fecha': '2026-07-08',
            'hora': '10:00',
            'servicio': 'Corte de cabello',
            'precio': '12000'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'registrada correctamente' in response.data

    def test_list_citas(self, logged_in_client):
        response = logged_in_client.get('/admin/citas')
        assert response.status_code == 200
        assert b'Citas' in response.data


class TestPromoLogic:
    def test_promo_martes_miercoles(self):
        from app import PROMO
        # Python weekday: 0=lun, 1=mar, 2=mier
        assert PROMO['dias_valido'] == [1, 2]
        assert PROMO['precio'] == 10000
        assert PROMO['activo'] is True

    def test_promo_price_calculation(self, client):
        from app import PROMO
        from datetime import date

        with app.app_context():
            db.create_all()
            if not Service.query.first():
                servicio = Service(nombre='Corte de cabello', precio=12000, duracion=30)
                db.session.add(servicio)
                db.session.commit()
            else:
                servicio = Service.query.first()

            fecha_miercoles = date(2026, 7, 8)
            dia_semana = fecha_miercoles.weekday()
            assert dia_semana == 2

            precio_normal = servicio.precio
            precio_promo = PROMO['precio'] if dia_semana in PROMO['dias_valido'] and 2 > 1 else precio_normal

            assert precio_promo == 10000
            assert precio_normal == 12000