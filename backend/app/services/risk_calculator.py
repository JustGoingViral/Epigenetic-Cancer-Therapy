"""
Genetic Risk Calculator for Predicting Gene Mutations and Epigenetic Factors

This service implements Bayesian inference and machine learning algorithms to calculate
the probability of genetic mutations and epigenetic risk factors based on patient responses.
"""

import math
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class GeneticRisk:
    """Data class for genetic risk assessments."""
    gene_symbol: str
    mutation_probability: float
    confidence_interval: Tuple[float, float]
    evidence_strength: str
    clinical_significance: str
    recommended_testing: List[str]

@dataclass
class EpigeneticFactor:
    """Data class for epigenetic risk factors."""
    factor_name: str
    risk_level: str
    probability_score: float
    modifiable: bool
    recommendations: List[str]

class GeneticRiskCalculator:
    """
    Advanced risk calculator using Bayesian inference and clinical evidence.
    """
    
    def __init__(self):
        """Initialize the genetic risk calculator."""
        self.genetic_priors = self._initialize_genetic_priors()
        self.epigenetic_factors = self._initialize_epigenetic_factors()
        self.symptom_gene_associations = self._initialize_symptom_associations()
        self.family_history_weights = self._initialize_family_history_weights()
        
    def calculate_genetic_risks(self, responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate genetic mutation probabilities based on questionnaire responses.
        
        Args:
            responses: List of patient responses
            
        Returns:
            List of genetic risk predictions
        """
        genetic_risks = []
        
        # Extract key information from responses
        family_history = self._extract_family_history(responses)
        symptoms = self._extract_symptoms(responses)
        demographics = self._extract_demographics(responses)
        medical_history = self._extract_medical_history(responses)
        
        # Calculate risks for major cancer genes
        high_risk_genes = [
            "BRCA1", "BRCA2", "TP53", "APC", "MLH1", "MSH2", "MSH6", "PMS2",
            "CHEK2", "ATM", "PALB2", "RAD51C", "RAD51D", "BRIP1", "CDH1",
            "PTEN", "STK11", "VHL", "RET", "NF1", "NF2", "TSC1", "TSC2"
        ]
        
        for gene in high_risk_genes:
            risk = self._calculate_gene_specific_risk(
                gene, family_history, symptoms, demographics, medical_history
            )
            
            if risk.mutation_probability > 0.05:  # Only include meaningful risks
                genetic_risks.append({
                    "gene_symbol": risk.gene_symbol,
                    "mutation_probability": risk.mutation_probability,
                    "confidence_interval": risk.confidence_interval,
                    "evidence_strength": risk.evidence_strength,
                    "clinical_significance": risk.clinical_significance,
                    "recommended_testing": risk.recommended_testing
                })
        
        # Sort by mutation probability (highest first)
        genetic_risks.sort(key=lambda x: x["mutation_probability"], reverse=True)
        
        return genetic_risks[:10]  # Return top 10 risks
    
    def calculate_epigenetic_risks(self, responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate epigenetic risk factors based on questionnaire responses.
        
        Args:
            responses: List of patient responses
            
        Returns:
            List of epigenetic risk factors
        """
        epigenetic_risks = []
        
        # Extract lifestyle and environmental factors
        lifestyle_factors = self._extract_lifestyle_factors(responses)
        environmental_exposures = self._extract_environmental_exposures(responses)
        dietary_patterns = self._extract_dietary_patterns(responses)
        stress_factors = self._extract_stress_factors(responses)
        
        # Calculate epigenetic factor risks
        factors_to_assess = [
            "dna_methylation_patterns",
            "histone_modification_patterns",
            "microrna_expression_patterns",
            "chromatin_accessibility_patterns",
            "telomere_health_markers",
            "cellular_stress_indicators",
            "inflammation_response_markers",
            "metabolic_regulation_patterns"
        ]
        
        for factor in factors_to_assess:
            risk = self._calculate_epigenetic_factor_risk(
                factor, lifestyle_factors, environmental_exposures, 
                dietary_patterns, stress_factors
            )
            
            if risk.probability_score > 0.1:  # Only include meaningful risks
                epigenetic_risks.append({
                    "factor_name": risk.factor_name,
                    "risk_level": risk.risk_level,
                    "probability_score": risk.probability_score,
                    "modifiable": risk.modifiable,
                    "recommendations": risk.recommendations
                })
        
        # Sort by probability score (highest first)
        epigenetic_risks.sort(key=lambda x: x["probability_score"], reverse=True)
        
        return epigenetic_risks
    
    def calculate_interim_risks(self, responses: List[Dict[str, Any]], questionnaire_type: str) -> Dict[str, float]:
        """
        Calculate interim risk scores during questionnaire completion.
        
        Args:
            responses: Current responses
            questionnaire_type: Type of questionnaire
            
        Returns:
            Dictionary of interim risk scores
        """
        interim_risks = {}
        
        if questionnaire_type in ["genetic_screening", "comprehensive_assessment"]:
            # Calculate preliminary genetic risks
            genetic_risks = self.calculate_genetic_risks(responses)
            if genetic_risks:
                top_genetic_risk = max(genetic_risks, key=lambda x: x["mutation_probability"])
                interim_risks["highest_genetic_risk"] = top_genetic_risk["mutation_probability"]
                interim_risks["genetic_risk_gene"] = top_genetic_risk["gene_symbol"]
        
        if questionnaire_type in ["epigenetic_assessment", "comprehensive_assessment"]:
            # Calculate preliminary epigenetic risks
            epigenetic_risks = self.calculate_epigenetic_risks(responses)
            if epigenetic_risks:
                top_epigenetic_risk = max(epigenetic_risks, key=lambda x: x["probability_score"])
                interim_risks["highest_epigenetic_risk"] = top_epigenetic_risk["probability_score"]
                interim_risks["epigenetic_risk_factor"] = top_epigenetic_risk["factor_name"]
        
        # Calculate overall preliminary risk
        if "highest_genetic_risk" in interim_risks and "highest_epigenetic_risk" in interim_risks:
            interim_risks["overall_risk"] = (
                interim_risks["highest_genetic_risk"] * 0.7 + 
                interim_risks["highest_epigenetic_risk"] * 0.3
            )
        elif "highest_genetic_risk" in interim_risks:
            interim_risks["overall_risk"] = interim_risks["highest_genetic_risk"] * 0.8
        elif "highest_epigenetic_risk" in interim_risks:
            interim_risks["overall_risk"] = interim_risks["highest_epigenetic_risk"] * 0.6
        
        return interim_risks
    
    # Private helper methods
    
    def _initialize_genetic_priors(self) -> Dict[str, float]:
        """Initialize prior probabilities for genetic mutations based on population data."""
        return {
            "BRCA1": 0.0024,  # ~1 in 400-500 for general population
            "BRCA2": 0.0020,  # ~1 in 500-600 for general population
            "TP53": 0.000020,  # Li-Fraumeni syndrome
            "APC": 0.0001,    # Familial adenomatous polyposis
            "MLH1": 0.00035,  # Lynch syndrome
            "MSH2": 0.00035,  # Lynch syndrome
            "MSH6": 0.00020,  # Lynch syndrome
            "PMS2": 0.00015,  # Lynch syndrome
            "CHEK2": 0.01,    # More common moderate risk gene
            "ATM": 0.0025,    # Ataxia telangiectasia
            "PALB2": 0.0024,  # BRCA2-associated
            "RAD51C": 0.0005, # Ovarian cancer susceptibility
            "RAD51D": 0.0005, # Ovarian cancer susceptibility
            "BRIP1": 0.0005,  # BRCA1-interacting protein
            "CDH1": 0.00002,  # Hereditary diffuse gastric cancer
            "PTEN": 0.00002,  # Cowden syndrome
            "STK11": 0.00002, # Peutz-Jeghers syndrome
            "VHL": 0.00004,   # Von Hippel-Lindau syndrome
            "RET": 0.00002,   # Multiple endocrine neoplasia
            "NF1": 0.0003,    # Neurofibromatosis type 1
            "NF2": 0.00003,   # Neurofibromatosis type 2
            "TSC1": 0.00001,  # Tuberous sclerosis
            "TSC2": 0.00002   # Tuberous sclerosis
        }
    
    def _initialize_epigenetic_factors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize epigenetic factor base risks and characteristics."""
        return {
            "dna_methylation_patterns": {
                "base_risk": 0.15,
                "modifiable": True,
                "lifestyle_impact": 0.4
            },
            "histone_modification_patterns": {
                "base_risk": 0.12,
                "modifiable": True,
                "lifestyle_impact": 0.3
            },
            "microrna_expression_patterns": {
                "base_risk": 0.18,
                "modifiable": True,
                "lifestyle_impact": 0.35
            },
            "chromatin_accessibility_patterns": {
                "base_risk": 0.08,
                "modifiable": False,
                "lifestyle_impact": 0.1
            },
            "telomere_health_markers": {
                "base_risk": 0.25,
                "modifiable": True,
                "lifestyle_impact": 0.6
            },
            "cellular_stress_indicators": {
                "base_risk": 0.45,
                "modifiable": True,
                "lifestyle_impact": 0.8
            },
            "inflammation_response_markers": {
                "base_risk": 0.35,
                "modifiable": True,
                "lifestyle_impact": 0.7
            },
            "metabolic_regulation_patterns": {
                "base_risk": 0.30,
                "modifiable": True,
                "lifestyle_impact": 0.75
            }
        }
    
    def _initialize_symptom_associations(self) -> Dict[str, Dict[str, float]]:
        """Initialize associations between symptoms and genes."""
        return {
            "breast_cancer_family": {
                "BRCA1": 0.8, "BRCA2": 0.7, "TP53": 0.4, "CHEK2": 0.3, "ATM": 0.25, "PALB2": 0.6
            },
            "ovarian_cancer_family": {
                "BRCA1": 0.9, "BRCA2": 0.6, "RAD51C": 0.5, "RAD51D": 0.5, "BRIP1": 0.4
            },
            "colorectal_cancer_family": {
                "APC": 0.7, "MLH1": 0.8, "MSH2": 0.8, "MSH6": 0.6, "PMS2": 0.5
            },
            "early_onset_cancer": {
                "TP53": 0.6, "BRCA1": 0.5, "BRCA2": 0.4, "CHEK2": 0.3
            },
            "multiple_primary_cancers": {
                "TP53": 0.8, "BRCA1": 0.4, "BRCA2": 0.4, "MLH1": 0.5, "MSH2": 0.5
            },
            "male_breast_cancer": {
                "BRCA2": 0.8, "BRCA1": 0.2, "CHEK2": 0.3, "PALB2": 0.4
            },
            "pancreatic_cancer_family": {
                "BRCA2": 0.6, "ATM": 0.4, "PALB2": 0.5, "CDKN2A": 0.3
            },
            "gastric_cancer_family": {
                "CDH1": 0.8, "APC": 0.2, "MLH1": 0.3, "MSH2": 0.3
            }
        }
    
    def _initialize_family_history_weights(self) -> Dict[str, float]:
        """Initialize weights for different family history patterns."""
        return {
            "first_degree_affected": 3.0,
            "second_degree_affected": 1.5,
            "third_degree_affected": 1.2,
            "multiple_affected": 2.5,
            "early_onset": 2.0,
            "bilateral_cancer": 3.5,
            "multiple_primary": 4.0,
            "ashkenazi_jewish": 1.8,
            "male_breast_cancer": 5.0
        }
    
    def _extract_family_history(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract family history information from responses."""
        family_history = {
            "cancer_types": [],
            "affected_relatives": [],
            "age_at_diagnosis": [],
            "patterns": []
        }
        
        for response in responses:
            question_id = response.get("question_id", "")
            answer = response.get("response")
            
            if "family" in question_id.lower() and "cancer" in question_id.lower():
                if isinstance(answer, str):
                    family_history["cancer_types"].append(answer.lower())
                elif isinstance(answer, list):
                    family_history["cancer_types"].extend([c.lower() for c in answer])
            
            elif "relative" in question_id.lower():
                if isinstance(answer, str):
                    family_history["affected_relatives"].append(answer.lower())
                elif isinstance(answer, list):
                    family_history["affected_relatives"].extend([r.lower() for r in answer])
            
            elif "age" in question_id.lower() and "diagnosis" in question_id.lower():
                if isinstance(answer, (int, float)):
                    family_history["age_at_diagnosis"].append(answer)
        
        # Identify patterns
        if "breast" in family_history["cancer_types"]:
            family_history["patterns"].append("breast_cancer_family")
        if "ovarian" in family_history["cancer_types"]:
            family_history["patterns"].append("ovarian_cancer_family")
        if "colorectal" in family_history["cancer_types"] or "colon" in family_history["cancer_types"]:
            family_history["patterns"].append("colorectal_cancer_family")
        if any(age < 50 for age in family_history["age_at_diagnosis"]):
            family_history["patterns"].append("early_onset_cancer")
        if len(family_history["cancer_types"]) > 2:
            family_history["patterns"].append("multiple_primary_cancers")
        
        return family_history
    
    def _extract_symptoms(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Extract symptom information from responses."""
        symptoms = []
        
        for response in responses:
            question_id = response.get("question_id", "")
            answer = response.get("response")
            
            if "symptom" in question_id.lower() or "sign" in question_id.lower():
                if isinstance(answer, str) and answer.lower() != "none":
                    symptoms.append(answer.lower())
                elif isinstance(answer, list):
                    symptoms.extend([s.lower() for s in answer if s.lower() != "none"])
        
        return symptoms
    
    def _extract_demographics(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract demographic information from responses."""
        demographics = {}
        
        for response in responses:
            question_id = response.get("question_id", "")
            answer = response.get("response")
            
            if "age" in question_id.lower():
                demographics["age"] = answer
            elif "gender" in question_id.lower() or "sex" in question_id.lower():
                demographics["gender"] = answer
            elif "ethnicity" in question_id.lower() or "ancestry" in question_id.lower():
                demographics["ethnicity"] = answer
        
        return demographics
    
    def _extract_medical_history(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract medical history from responses."""
        medical_history = {
            "previous_cancers": [],
            "surgeries": [],
            "medications": [],
            "chronic_conditions": []
        }
        
        for response in responses:
            question_id = response.get("question_id", "")
            answer = response.get("response")
            
            if "previous" in question_id.lower() and "cancer" in question_id.lower():
                if isinstance(answer, str) and answer.lower() != "none":
                    medical_history["previous_cancers"].append(answer.lower())
                elif isinstance(answer, list):
                    medical_history["previous_cancers"].extend([c.lower() for c in answer])
            
            elif "surgery" in question_id.lower():
                if isinstance(answer, str) and answer.lower() != "none":
                    medical_history["surgeries"].append(answer.lower())
                elif isinstance(answer, list):
                    medical_history["surgeries"].extend([s.lower() for s in answer])
        
        return medical_history
    
    def _extract_lifestyle_factors(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract lifestyle factors from responses."""
        lifestyle = {
            "smoking": False,
            "alcohol_consumption": "none",
            "exercise_frequency": "none",
            "diet_quality": "average",
            "sleep_quality": "average",
            "stress_level": "moderate"
        }
        
        for response in responses:
            question_id = response.get("question_id", "")
            answer = response.get("response")
            
            if "smoking" in question_id.lower():
                lifestyle["smoking"] = answer if isinstance(answer, bool) else answer.lower() == "yes"
            elif "alcohol" in question_id.lower():
                lifestyle["alcohol_consumption"] = answer
            elif "exercise" in question_id.lower():
                lifestyle["exercise_frequency"] = answer
            elif "diet" in question_id.lower():
                lifestyle["diet_quality"] = answer
            elif "sleep" in question_id.lower():
                lifestyle["sleep_quality"] = answer
            elif "stress" in question_id.lower():
                lifestyle["stress_level"] = answer
        
        return lifestyle
    
    def _extract_environmental_exposures(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Extract environmental exposure information."""
        exposures = []
        
        for response in responses:
            question_id = response.get("question_id", "")
            answer = response.get("response")
            
            if "exposure" in question_id.lower() or "environmental" in question_id.lower():
                if isinstance(answer, str) and answer.lower() != "none":
                    exposures.append(answer.lower())
                elif isinstance(answer, list):
                    exposures.extend([e.lower() for e in answer if e.lower() != "none"])
        
        return exposures
    
    def _extract_dietary_patterns(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract dietary pattern information."""
        dietary = {
            "processed_food_frequency": "moderate",
            "vegetable_intake": "moderate",
            "fruit_intake": "moderate",
            "whole_grain_consumption": "moderate",
            "red_meat_consumption": "moderate"
        }
        
        for response in responses:
            question_id = response.get("question_id", "")
            answer = response.get("response")
            
            if "processed" in question_id.lower() and "food" in question_id.lower():
                dietary["processed_food_frequency"] = answer
            elif "vegetable" in question_id.lower():
                dietary["vegetable_intake"] = answer
            elif "fruit" in question_id.lower():
                dietary["fruit_intake"] = answer
            elif "grain" in question_id.lower():
                dietary["whole_grain_consumption"] = answer
            elif "meat" in question_id.lower():
                dietary["red_meat_consumption"] = answer
        
        return dietary
    
    def _extract_stress_factors(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract stress and psychological factors."""
        stress_factors = {
            "chronic_stress": False,
            "major_life_events": [],
            "mental_health_history": "none",
            "social_support": "adequate"
        }
        
        for response in responses:
            question_id = response.get("question_id", "")
            answer = response.get("response")
            
            if "stress" in question_id.lower():
                if isinstance(answer, bool):
                    stress_factors["chronic_stress"] = answer
                else:
                    stress_factors["chronic_stress"] = answer.lower() in ["yes", "high", "severe"]
            elif "life_event" in question_id.lower():
                if isinstance(answer, list):
                    stress_factors["major_life_events"] = answer
            elif "mental_health" in question_id.lower():
                stress_factors["mental_health_history"] = answer
            elif "support" in question_id.lower():
                stress_factors["social_support"] = answer
        
        return stress_factors
    
    def _calculate_gene_specific_risk(
        self, 
        gene: str, 
        family_history: Dict[str, Any], 
        symptoms: List[str], 
        demographics: Dict[str, Any], 
        medical_history: Dict[str, Any]
    ) -> GeneticRisk:
        """Calculate risk for a specific gene using Bayesian inference."""
        # Start with prior probability
        prior_prob = self.genetic_priors.get(gene, 0.001)
        
        # Calculate likelihood based on family history
        family_likelihood = self._calculate_family_history_likelihood(gene, family_history)
        
        # Calculate likelihood based on demographics
        demo_likelihood = self._calculate_demographic_likelihood(gene, demographics)
        
        # Calculate likelihood based on symptoms
        symptom_likelihood = self._calculate_symptom_likelihood(gene, symptoms)
        
        # Calculate likelihood based on medical history
        medical_likelihood = self._calculate_medical_history_likelihood(gene, medical_history)
        
        # Combine likelihoods using Bayesian inference
        posterior_prob = self._bayesian_update(
            prior_prob, 
            [family_likelihood, demo_likelihood, symptom_likelihood, medical_likelihood]
        )
        
        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(posterior_prob)
        
        # Determine evidence strength
        evidence_strength = self._determine_evidence_strength(
            family_likelihood, demo_likelihood, symptom_likelihood, medical_likelihood
        )
        
        # Generate clinical significance
        clinical_significance = self._generate_clinical_significance(gene, posterior_prob)
        
        # Recommend testing based on risk
        recommended_testing = self._recommend_genetic_testing(gene, posterior_prob)
        
        return GeneticRisk(
            gene_symbol=gene,
            mutation_probability=min(0.99, max(0.001, posterior_prob)),
            confidence_interval=confidence_interval,
            evidence_strength=evidence_strength,
            clinical_significance=clinical_significance,
            recommended_testing=recommended_testing
        )
    
    def _calculate_epigenetic_factor_risk(
        self, 
        factor: str, 
        lifestyle_factors: Dict[str, Any], 
        environmental_exposures: List[str], 
        dietary_patterns: Dict[str, Any], 
        stress_factors: Dict[str, Any]
    ) -> EpigeneticFactor:
        """Calculate risk for a specific epigenetic factor."""
        factor_info = self.epigenetic_factors.get(factor, {})
        base_risk = factor_info.get("base_risk", 0.1)
        lifestyle_impact = factor_info.get("lifestyle_impact", 0.3)
        
        # Calculate lifestyle modification factor
        lifestyle_modifier = self._calculate_lifestyle_modifier(
            lifestyle_factors, dietary_patterns, stress_factors
        )
        
        # Calculate environmental modifier
        environmental_modifier = self._calculate_environmental_modifier(environmental_exposures)
        
        # Combine factors
        final_risk = base_risk * (1 + lifestyle_modifier * lifestyle_impact + environmental_modifier * 0.2)
        final_risk = min(0.95, max(0.05, final_risk))
        
        # Determine risk level
        if final_risk < 0.3:
            risk_level = "low"
        elif final_risk < 0.6:
            risk_level = "moderate"
        else:
            risk_level = "high"
        
        # Generate recommendations
        recommendations = self._generate_epigenetic_recommendations(
            factor, lifestyle_factors, dietary_patterns, stress_factors
        )
        
        return EpigeneticFactor(
            factor_name=factor.replace("_", " ").title(),
            risk_level=risk_level,
            probability_score=final_risk,
            modifiable=factor_info.get("modifiable", True),
            recommendations=recommendations
        )
    
    def _bayesian_update(self, prior: float, likelihoods: List[float]) -> float:
        """Perform Bayesian update with multiple likelihood ratios."""
        # Convert to log space for numerical stability
        log_odds = math.log(prior / (1 - prior))
        
        for likelihood in likelihoods:
            if likelihood > 0:
                log_odds += math.log(likelihood)
        
        # Convert back to probability
        odds = math.exp(log_odds)
        posterior = odds / (1 + odds)
        
        return posterior
    
    def _calculate_family_history_likelihood(self, gene: str, family_history: Dict[str, Any]) -> float:
        """Calculate likelihood ratio based on family history."""
        likelihood = 1.0
        
        for pattern in family_history.get("patterns", []):
            if pattern in self.symptom_gene_associations:
                gene_weight = self.symptom_gene_associations[pattern].get(gene, 0)
                if gene_weight > 0:
                    likelihood *= (1 + gene_weight)
        
        # Additional weights for specific family history characteristics
        if family_history.get("affected_relatives"):
            num_affected = len(family_history["affected_relatives"])
            if num_affected >= 2:
                likelihood *= (1 + num_affected * 0.3)
        
        return likelihood
    
    def _calculate_demographic_likelihood(self, gene: str, demographics: Dict[str, Any]) -> float:
        """Calculate likelihood ratio based on demographics."""
        likelihood = 1.0
        
        # Age adjustments
        age = demographics.get("age")
        if age:
            if gene in ["BRCA1", "BRCA2"] and age < 50:
                likelihood *= 1.5
            elif gene == "TP53" and age < 30:
                likelihood *= 2.0
        
        # Ethnicity adjustments
        ethnicity = demographics.get("ethnicity", "").lower()
        if "ashkenazi" in ethnicity and gene in ["BRCA1", "BRCA2"]:
            likelihood *= 1.8
        
        # Gender adjustments
        gender = demographics.get("gender", "").lower()
        if gender == "male" and gene == "BRCA2":
            likelihood *= 1.3
        
        return likelihood
    
    def _calculate_symptom_likelihood(self, gene: str, symptoms: List[str]) -> float:
        """Calculate likelihood ratio based on symptoms."""
        likelihood = 1.0
        
        # This would be expanded with more sophisticated symptom-gene associations
        cancer_related_symptoms = [
            "unexplained_weight_loss", "fatigue", "pain", "lumps", "bleeding"
        ]
        
        symptom_count = sum(1 for symptom in symptoms if any(s in symptom for s in cancer_related_symptoms))
        
        if symptom_count > 0:
            likelihood *= (1 + symptom_count * 0.2)
        
        return likelihood
    
    def _calculate_medical_history_likelihood(self, gene: str, medical_history: Dict[str, Any]) -> float:
        """Calculate likelihood ratio based on medical history."""
        likelihood = 1.0
        
        # Previous cancer history
        previous_cancers = medical_history.get("previous_cancers", [])
        if previous_cancers:
            likelihood *= 1.8
        
        # Multiple primary cancers
        if len(previous_cancers) > 1:
            likelihood *= 2.5
        
        return likelihood
    
    def _calculate_confidence_interval(self, probability: float) -> Tuple[float, float]:
        """Calculate confidence interval for probability estimate."""
        # Simple confidence interval calculation
        margin = 0.1 * probability  # 10% margin
        lower_bound = max(0.001, probability - margin)
        upper_bound = min(0.999, probability + margin)
        
        return (lower_bound, upper_bound)
    
    def _determine_evidence_strength(self, *likelihoods: float) -> str:
        """Determine strength of evidence based on likelihood ratios."""
        max_likelihood = max(likelihoods)
        
        if max_likelihood > 3.0:
            return "very_high"
        elif max_likelihood > 2.0:
            return "high"
        elif max_likelihood > 1.5:
            return "moderate"
        else:
            return "low"
    
    def _generate_clinical_significance(self, gene: str, probability: float) -> str:
        """Generate clinical significance description."""
        if probability > 0.3:
            return f"High probability of {gene} mutation warrants immediate genetic counseling"
        elif probability > 0.1:
            return f"Moderate probability of {gene} mutation suggests consideration of genetic testing"
        elif probability > 0.05:
            return f"Low-moderate probability of {gene} mutation may warrant discussion with genetic counselor"
        else:
            return f"Low probability of {gene} mutation based on current information"
    
    def _recommend_genetic_testing(self, gene: str, probability: float) -> List[str]:
        """Recommend genetic testing based on risk level."""
        recommendations = []
        
        if probability > 0.3:
            recommendations.extend([
                f"Urgent genetic counseling for {gene} testing",
                "Multi-gene panel testing including high-risk genes",
                "Family cascade testing if positive"
            ])
        elif probability > 0.1:
            recommendations.extend([
                f"Genetic counseling to discuss {gene} testing",
                "Consider single-gene or targeted panel testing"
            ])
        elif probability > 0.05:
            recommendations.extend([
                f"Discussion with genetic counselor about {gene} risk",
                "Consider testing based on additional clinical factors"
            ])
        
        return recommendations
    
    def _calculate_lifestyle_modifier(
        self, 
        lifestyle_factors: Dict[str, Any], 
        dietary_patterns: Dict[str, Any], 
        stress_factors: Dict[str, Any]
    ) -> float:
        """Calculate lifestyle modification factor for epigenetic risks."""
        modifier = 0.0
        
        # Smoking impact
        if lifestyle_factors.get("smoking", False):
            modifier += 0.4
        
        # Alcohol consumption
        alcohol = lifestyle_factors.get("alcohol_consumption", "none").lower()
        if alcohol in ["heavy", "daily", "excessive"]:
            modifier += 0.3
        elif alcohol in ["moderate", "weekly"]:
            modifier += 0.1
        
        # Exercise frequency (protective)
        exercise = lifestyle_factors.get("exercise_frequency", "none").lower()
        if exercise in ["daily", "5+ times per week"]:
            modifier -= 0.2
        elif exercise in ["regular", "3-4 times per week"]:
            modifier -= 0.1
        
        # Diet quality (protective if good)
        diet = lifestyle_factors.get("diet_quality", "average").lower()
        if diet in ["excellent", "very good"]:
            modifier -= 0.15
        elif diet in ["poor", "very poor"]:
            modifier += 0.2
        
        # Sleep quality
        sleep = lifestyle_factors.get("sleep_quality", "average").lower()
        if sleep in ["poor", "very poor"]:
            modifier += 0.15
        
        # Stress levels
        stress = lifestyle_factors.get("stress_level", "moderate").lower()
        if stress in ["high", "severe", "chronic"]:
            modifier += 0.25
        
        # Dietary patterns
        if dietary_patterns.get("processed_food_frequency", "moderate").lower() in ["high", "daily"]:
            modifier += 0.15
        
        if dietary_patterns.get("vegetable_intake", "moderate").lower() in ["high", "daily"]:
            modifier -= 0.1
        
        # Stress factors
        if stress_factors.get("chronic_stress", False):
            modifier += 0.2
        
        return modifier
    
    def _calculate_environmental_modifier(self, environmental_exposures: List[str]) -> float:
        """Calculate environmental exposure modification factor."""
        modifier = 0.0
        
        high_risk_exposures = [
            "asbestos", "radiation", "benzene", "formaldehyde", 
            "pesticides", "heavy_metals", "industrial_chemicals"
        ]
        
        moderate_risk_exposures = [
            "air_pollution", "secondhand_smoke", "occupational_dust"
        ]
        
        for exposure in environmental_exposures:
            exposure_lower = exposure.lower()
            if any(risk in exposure_lower for risk in high_risk_exposures):
                modifier += 0.3
            elif any(risk in exposure_lower for risk in moderate_risk_exposures):
                modifier += 0.15
        
        return min(1.0, modifier)  # Cap at 1.0
    
    def _generate_epigenetic_recommendations(
        self, 
        factor: str, 
        lifestyle_factors: Dict[str, Any], 
        dietary_patterns: Dict[str, Any], 
        stress_factors: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for epigenetic risk factors."""
        recommendations = []
        
        # General recommendations based on factor type
        if "dna_methylation" in factor:
            recommendations.extend([
                "Increase folate and B-vitamin intake",
                "Consider Mediterranean diet pattern",
                "Limit alcohol consumption"
            ])
        
        elif "histone_modification" in factor:
            recommendations.extend([
                "Regular physical exercise",
                "Stress management techniques",
                "Adequate sleep (7-9 hours nightly)"
            ])
        
        elif "oxidative_stress" in factor:
            recommendations.extend([
                "Increase antioxidant-rich foods",
                "Reduce processed food consumption",
                "Consider antioxidant supplementation under medical guidance"
            ])
        
        elif "inflammation" in factor:
            recommendations.extend([
                "Anti-inflammatory diet (omega-3 rich foods)",
                "Regular moderate exercise",
                "Stress reduction techniques"
            ])
        
        elif "telomere" in factor:
            recommendations.extend([
                "Regular aerobic exercise",
                "Stress management and meditation",
                "Adequate sleep and recovery"
            ])
        
        # Lifestyle-specific recommendations
        if lifestyle_factors.get("smoking", False):
            recommendations.append("Smoking cessation program")
        
        if lifestyle_factors.get("stress_level", "").lower() in ["high", "severe"]:
            recommendations.extend([
                "Professional stress management counseling",
                "Mindfulness or meditation practice"
            ])
        
        if dietary_patterns.get("processed_food_frequency", "").lower() in ["high", "daily"]:
            recommendations.append("Reduce processed food consumption")
        
        return recommendations[:5]  # Limit to top 5 recommendations
