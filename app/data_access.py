from typing import Optional
from .supabase_client import get_supabase
from .models import Paciente, Atencion, User


def get_active_atenciones():
    supabase = get_supabase()
    res = supabase.table("atenciones").select("*").eq("activa", True).order("creado_en", desc=True).execute()
    return [Atencion.from_dict(r) for r in (res.data or [])]


def get_atencion(atencion_id: str) -> Optional[Atencion]:
    supabase = get_supabase()
    res = supabase.table("atenciones").select("*").eq("id", atencion_id).single().execute()
    data = res.data
    return Atencion.from_dict(data) if data else None


def update_atencion(atencion_id: str, values: dict):
    supabase = get_supabase()
    supabase.table("atenciones").update(values).eq("id", atencion_id).execute()


def create_atencion(values: dict) -> Atencion:
    supabase = get_supabase()
    res = supabase.table("atenciones").insert(values).execute()
    return Atencion.from_dict(res.data[0])


def get_paciente_by_run(run: str) -> Optional[Paciente]:
    supabase = get_supabase()
    res = supabase.table("pacientes").select("*").eq("run", run).single().execute()
    data = res.data
    return Paciente.from_dict(data) if data else None


def get_paciente(paciente_id: str) -> Optional[Paciente]:
    supabase = get_supabase()
    res = supabase.table("pacientes").select("*").eq("id", paciente_id).single().execute()
    data = res.data
    return Paciente.from_dict(data) if data else None


def create_paciente(values: dict) -> Paciente:
    supabase = get_supabase()
    res = supabase.table("pacientes").insert(values).execute()
    return Paciente.from_dict(res.data[0])


def update_paciente(paciente_id: str, values: dict):
    supabase = get_supabase()
    supabase.table("pacientes").update(values).eq("id", paciente_id).execute()


def get_user_by_email(email: str) -> Optional[User]:
    supabase = get_supabase()
    res = supabase.table("users").select("*").eq("email", email).single().execute()
    data = res.data
    return User.from_dict(data) if data else None


def get_user_by_id(user_id: str) -> Optional[User]:
    supabase = get_supabase()
    res = supabase.table("users").select("*").eq("id", user_id).single().execute()
    data = res.data
    return User.from_dict(data) if data else None


def create_user(values: dict) -> User:
    supabase = get_supabase()
    res = supabase.table("users").insert(values).execute()
    return User.from_dict(res.data[0])

