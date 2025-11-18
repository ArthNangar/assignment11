# app/models/calculation.py
from datetime import datetime
import uuid
from typing import List
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declared_attr
from app.database import Base


class AbstractCalculation:
    @declared_attr
    def __tablename__(cls):
        """All calculation types share the 'calculations' table"""
        return 'calculations'

    @declared_attr
    def id(cls):
        """Unique identifier for each calculation (UUID for distribution)"""
        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False
        )

    @declared_attr
    def user_id(cls):
        """
        Foreign key to the user who owns this calculation.
        
        CASCADE delete ensures calculations are deleted when user is deleted.
        Index improves query performance when filtering by user_id.
        """
        return Column(
            UUID(as_uuid=True),
            ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        )

    @declared_attr
    def type(cls):
        return Column(
            String(50),
            nullable=False,
            index=True
        )

    @declared_attr
    def inputs(cls):
        return Column(
            JSON,
            nullable=False
        )

    @declared_attr
    def result(cls):
        return Column(
            Float,
            nullable=True
        )

    @declared_attr
    def created_at(cls):
        """Timestamp when the calculation was created"""
        return Column(
            DateTime,
            default=datetime.utcnow,
            nullable=False
        )

    @declared_attr
    def updated_at(cls):
        """Timestamp when the calculation was last updated"""
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )

    @declared_attr
    def user(cls):
        return relationship("User", back_populates="calculations")

    @classmethod
    def create(cls, calculation_type: str, user_id: uuid.UUID,
               inputs: List[float]) -> "Calculation":
        calculation_classes = {
            'addition': Addition,
            'subtraction': Subtraction,
            'multiplication': Multiplication,
            'division': Division,
        }
        calculation_class = calculation_classes.get(calculation_type.lower())
        if not calculation_class:
            raise ValueError(
                f"Unsupported calculation type: {calculation_type}"
            )
        return calculation_class(user_id=user_id, inputs=inputs)

    def get_result(self) -> float:
        raise NotImplementedError(
            "Subclasses must implement get_result() method"
        )

    def __repr__(self):
        return f"<Calculation(type={self.type}, inputs={self.inputs})>"


class Calculation(Base, AbstractCalculation):
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "calculation",
    }


class Addition(Calculation):
    __mapper_args__ = {"polymorphic_identity": "addition"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError(
                "Inputs must be a list with at least two numbers."
            )
        return sum(self.inputs)


class Subtraction(Calculation):
    __mapper_args__ = {"polymorphic_identity": "subtraction"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError(
                "Inputs must be a list with at least two numbers."
            )
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result -= value
        return result


class Multiplication(Calculation):
    __mapper_args__ = {"polymorphic_identity": "multiplication"}

    def get_result(self) -> float:
        """
        Calculate the product of all input numbers.
        
        Returns:
            The product of all inputs
            
        Raises:
            ValueError: If inputs is not a list or has fewer than 2 numbers
        """
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError(
                "Inputs must be a list with at least two numbers."
            )
        result = 1
        for value in self.inputs:
            result *= value
        return result


class Division(Calculation):
    __mapper_args__ = {"polymorphic_identity": "division"}

    def get_result(self) -> float:
        """
        Divide the first number by all subsequent numbers sequentially.
        
        Returns:
            The result of sequential division
            
        Raises:
            ValueError: If inputs is not a list, has fewer than 2 numbers,
                       or if attempting to divide by zero
        """
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError(
                "Inputs must be a list with at least two numbers."
            )
        result = self.inputs[0]
        for value in self.inputs[1:]:
            if value == 0:
                raise ValueError("Cannot divide by zero.")
            result /= value
        return result
