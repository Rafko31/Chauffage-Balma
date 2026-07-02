from datetime import datetime, UTC
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Table, Enum as SQLEnum, UniqueConstraint, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)

class UserRole(str, Enum):
    SYSADMIN = "pulse_ia_sysadmin"
    ORGADMIN = "org_admin"
    PROGRAM_MANAGER = "program_manager"
    DIRECTION = "direction"
    GESTIONNAIRE = "gestionnaire"
    REPONDANT = "repondant"

class AdoptionState(str, Enum):
    EXPOSITION = "Exposition"
    EXPLORATION = "Exploration"
    EXPERIMENTATION = "Expérimentation"
    USAGE_UTILE = "Usage utile"
    INTEGRATION = "Intégration"
    DIFFUSION = "Diffusion"

class UsageStatus(str, Enum):
    IDEE = "Idée"
    A_ETUDIER = "À étudier"
    EN_EXPERIMENTATION = "En expérimentation"
    CONCLUANTE = "Concluante"
    USAGE_RECURRENT = "Usage récurrent"
    DIFFUSEE = "Diffusée"

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    is_active: Mapped[bool] = mapped_column(default=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict) # e.g. anonymity_threshold

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole))
    is_active: Mapped[bool] = mapped_column(default=True)

    organization = relationship("Organization")

class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("org_id", "external_id", name="uq_participant_org_external_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True) # CRM/RH ID
    email: Mapped[Optional[str]] = mapped_column(String(255))

    # Segments
    population: Mapped[Optional[str]] = mapped_column(String(255))
    direction: Mapped[Optional[str]] = mapped_column(String(255))
    service: Mapped[Optional[str]] = mapped_column(String(255))
    equipe: Mapped[Optional[str]] = mapped_column(String(255))
    gestionnaire_id: Mapped[Optional[str]] = mapped_column(String(255))
    segment_client: Mapped[Optional[str]] = mapped_column(String(255))
    localisation: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class ReportStatus(str, Enum):
    BROUILLON = "Brouillon"
    EN_REVISION = "En révision"
    APPROUVE = "Approuvé"
    PUBLIE = "Publié"

class AssessmentTemplate(Base):
    __tablename__ = "assessment_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

class AssessmentVersion(Base):
    __tablename__ = "assessment_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("assessment_templates.id"))
    version: Mapped[str] = mapped_column(String(50))
    structure: Mapped[dict] = mapped_column(JSON) # Questions, Options, etc.
    scoring_rules: Mapped[dict] = mapped_column(JSON) # Weights and rules
    is_frozen: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    assessment_version_id: Mapped[int] = mapped_column(ForeignKey("assessment_versions.id"))
    title: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[datetime] = mapped_column()
    end_date: Mapped[Optional[datetime]] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    status: Mapped[ReportStatus] = mapped_column(SQLEnum(ReportStatus), default=ReportStatus.BROUILLON)
    assessment_version_id: Mapped[int] = mapped_column(ForeignKey("assessment_versions.id"))
    content: Mapped[dict] = mapped_column(JSON) # Snapshot of data, scores, and recommendations
    version: Mapped[str] = mapped_column(String(50))
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    published_at: Mapped[Optional[datetime]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class ParticipationStatus(Base):
    """Tracks WHO participated without linking to WHAT they answered.
    Using a hash (campaign_id, participant_id, salt) to prevent direct link.
    """
    __tablename__ = "participation_statuses"
    __table_args__ = (
        UniqueConstraint("campaign_id", "participant_hash", name="uq_participation_hash"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    participant_hash: Mapped[str] = mapped_column(String(64), index=True)
    responded_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

class Consent(Base):
    """Stores consent details separately from answers."""
    __tablename__ = "consents"
    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    consent_text_version: Mapped[str] = mapped_column(String(50))
    mode: Mapped[str] = mapped_column(String(20)) # "identified" or "anonymous"
    given_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

class IdentifiedAnswer(Base):
    __tablename__ = "identified_answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    answers: Mapped[dict] = mapped_column(JSON) # Detailed answers
    computed_scores: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

class AnonymousAnswer(Base):
    """Absolutely NO link to participant_id."""
    __tablename__ = "anonymous_answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))

    # Metadata for segments (copied from participant at the time of answer)
    population: Mapped[Optional[str]] = mapped_column(String(255))
    direction: Mapped[Optional[str]] = mapped_column(String(255))
    service: Mapped[Optional[str]] = mapped_column(String(255))
    equipe: Mapped[Optional[str]] = mapped_column(String(255))
    localisation: Mapped[Optional[str]] = mapped_column(String(255))

    answers: Mapped[dict] = mapped_column(JSON)
    computed_scores: Mapped[dict] = mapped_column(JSON)

    # Decoupled timestamp to prevent temporal correlation
    # Jittering is applied at the service layer
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

class FollowUpRequest(Base):
    """Isolated from answers."""
    __tablename__ = "follow_up_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    contact_info: Mapped[str] = mapped_column(String(512))
    message: Mapped[Optional[str]] = mapped_column(String(1024))
    is_anonymous_respondent: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

class UseCase(Base):
    """Registre léger des cas d'usage."""
    __tablename__ = "use_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[UsageStatus] = mapped_column(SQLEnum(UsageStatus))
    population: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
