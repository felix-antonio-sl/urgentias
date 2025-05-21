import pytest
from app.models import Paciente

VALID_RUNS = [
    "123456-7",
    "1234567-8",
    "12345678-9",
    "12345678-K",
    "12345678-k",
]

INVALID_RUNS = [
    "12345-5",
    "123456789-0",
    "1234567",
    "12345678",
    "12345678-55",
    "1234567k",
    "abcdefgh-k",
    "12345678/5",
]

@pytest.mark.parametrize("run", VALID_RUNS)
def test_validar_run_valido(run):
    assert Paciente.validar_run(run) is True

@pytest.mark.parametrize("run", INVALID_RUNS)
def test_validar_run_invalido(run):
    assert Paciente.validar_run(run) is False
