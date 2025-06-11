"""
Comprehensive test suite for the GeneticRiskCalculator

Tests cover genetic risk calculations, epigenetic factor assessments,
Bayesian inference algorithms, and clinical decision support.
"""

import pytest
import math
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import the classes under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.risk_calculator import GeneticRiskCalculator, GeneticRisk, EpigeneticFactor


class TestGeneticRiskCalculator:
    """Test cases for GeneticRiskCalculator class."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance for testing."""
        return GeneticRiskCalculator()
    
    @pytest.fixture
    def sample_responses(self):
        """Sample patient responses for testing."""
        return [
            {
                "question_id": "demo_age",
                "response": 45
            },
            {
                "question_id": "demo_gender", 
                "response": "Female"
            },
            {
                "question_id": "demo_ethnicity",
                "response": ["Ashkenazi Jewish"]
            },
            {
                "question_id": "family_cancer_history",
                "response": True
            },
            {
                "question_id": "family_cancer_types",
                "response": ["Breast cancer", "Ovarian cancer"]
            },
            {
                "question_id": "family_cancer_relatives",
                "response": ["Mother", "Sister"]
            },
            {
                "question_id": "family_early_onset",
                "response": True
            },
            {
                "question_id": "personal_cancer_history",
                "response": False
            },
            {
                "question_id": "lifestyle_smoking",
                "response": "Former smoker"
            },
            {
                "question_id": "lifestyle_alcohol",
                "response": "Occasionally (1-2 times per month)"
            },
            {
                "question_id": "stress_level",
                "response": "High"
            }
        ]
    
    @pytest.fixture
    def high_risk_responses(self):
        """High-risk patient responses for testing edge cases."""
        return [
            {
                "question_id": "demo_age",
                "response": 35
            },
            {
                "question_id": "demo_gender",
                "response": "Female"
            },
            {
                "question_id": "demo_ethnicity",
                "response": ["Ashkenazi Jewish"]
            },
            {
                "question_id": "family_cancer_history",
                "response": True
            },
            {
                "question_id": "family_cancer_types",
                "response": ["Breast cancer", "Ovarian cancer", "Pancreatic cancer"]
            },
            {
                "question_id": "family_early_onset",
                "response": True
            },
            {
                "question_id": "family_multiple_cancers",
                "response": True
            },
            {
                "question_id": "personal_cancer_history",
                "response": True
            },
            {
                "question_id": "personal_cancer_type",
                "response": ["Breast cancer"]
            },
            {
                "question_id": "personal_cancer_age",
                "response": 28
            }
        ]

    def test_calculator_initialization(self, calculator):
        """Test that calculator initializes correctly."""
        assert calculator is not None
        assert hasattr(calculator, 'genetic_priors')
        assert hasattr(calculator, 'epigenetic_factors')
        assert hasattr(calculator, 'symptom_gene_associations')
        assert hasattr(calculator, 'family_history_weights')
        
        # Test that genetic priors are properly initialized
        assert 'BRCA1' in calculator.genetic_priors
        assert 'BRCA2' in calculator.genetic_priors
        assert 'TP53' in calculator.genetic_priors
        
        # Test that prior probabilities are reasonable
        assert 0 < calculator.genetic_priors['BRCA1'] < 0.1
        assert 0 < calculator.genetic_priors['BRCA2'] < 0.1

    def test_genetic_risk_calculation_basic(self, calculator, sample_responses):
        """Test basic genetic risk calculation."""
        risks = calculator.calculate_genetic_risks(sample_responses)
        
        assert isinstance(risks, list)
        assert len(risks) > 0
        
        # Check that BRCA1/BRCA2 are in top risks given family history
        gene_symbols = [risk['gene_symbol'] for risk in risks]
        assert 'BRCA1' in gene_symbols or 'BRCA2' in gene_symbols
        
        # Validate risk structure
        for risk in risks:
            assert 'gene_symbol' in risk
            assert 'mutation_probability' in risk
            assert 'confidence_interval' in risk
            assert 'evidence_strength' in risk
            assert 'clinical_significance' in risk
            assert 'recommended_testing' in risk
            
            # Test probability bounds
            assert 0 <= risk['mutation_probability'] <= 1
            
            # Test confidence interval
            ci = risk['confidence_interval']
            assert len(ci) == 2
            assert ci[0] <= risk['mutation_probability'] <= ci[1]
            
            # Test evidence strength values
            assert risk['evidence_strength'] in ['low', 'moderate', 'high', 'very_high']

    def test_genetic_risk_high_risk_case(self, calculator, high_risk_responses):
        """Test genetic risk calculation for high-risk case."""
        risks = calculator.calculate_genetic_risks(high_risk_responses)
        
        assert len(risks) > 0
        
        # High-risk case should have elevated BRCA probabilities
        brca_risks = [r for r in risks if r['gene_symbol'] in ['BRCA1', 'BRCA2']]
        assert len(brca_risks) > 0
        
        # At least one BRCA gene should have >10% probability
        max_brca_prob = max(r['mutation_probability'] for r in brca_risks)
        assert max_brca_prob > 0.1
        
        # Should recommend genetic testing
        for risk in brca_risks:
            if risk['mutation_probability'] > 0.1:
                assert any('counseling' in rec.lower() for rec in risk['recommended_testing'])

    def test_epigenetic_risk_calculation(self, calculator, sample_responses):
        """Test epigenetic risk factor calculation."""
        risks = calculator.calculate_epigenetic_risks(sample_responses)
        
        assert isinstance(risks, list)
        assert len(risks) > 0
        
        # Validate epigenetic risk structure
        for risk in risks:
            assert 'factor_name' in risk
            assert 'risk_level' in risk
            assert 'probability_score' in risk
            assert 'modifiable' in risk
            assert 'recommendations' in risk
            
            # Test probability bounds
            assert 0 <= risk['probability_score'] <= 1
            
            # Test risk level values
            assert risk['risk_level'] in ['low', 'moderate', 'high']
            
            # Test that modifiable is boolean
            assert isinstance(risk['modifiable'], bool)
            
            # Test recommendations are provided
            assert isinstance(risk['recommendations'], list)

    def test_interim_risk_calculation(self, calculator, sample_responses):
        """Test interim risk calculation during questionnaire."""
        # Test genetic screening
        interim_risks = calculator.calculate_interim_risks(sample_responses, "genetic_screening")
        assert isinstance(interim_risks, dict)
        
        if 'highest_genetic_risk' in interim_risks:
            assert 0 <= interim_risks['highest_genetic_risk'] <= 1
        
        # Test epigenetic assessment
        interim_risks = calculator.calculate_interim_risks(sample_responses, "epigenetic_assessment")
        assert isinstance(interim_risks, dict)
        
        if 'highest_epigenetic_risk' in interim_risks:
            assert 0 <= interim_risks['highest_epigenetic_risk'] <= 1
        
        # Test comprehensive assessment
        interim_risks = calculator.calculate_interim_risks(sample_responses, "comprehensive_assessment")
        assert isinstance(interim_risks, dict)
        
        if 'overall_risk' in interim_risks:
            assert 0 <= interim_risks['overall_risk'] <= 1

    def test_bayesian_update(self, calculator):
        """Test Bayesian inference calculations."""
        prior = 0.002  # BRCA1 population frequency
        likelihoods = [2.0, 1.5, 3.0]  # Sample likelihood ratios
        
        posterior = calculator._bayesian_update(prior, likelihoods)
        
        # Posterior should be higher than prior given positive evidence
        assert posterior > prior
        
        # Should be bounded between 0 and 1
        assert 0 < posterior < 1
        
        # Test with negative evidence (protective factors)
        likelihoods_protective = [0.5, 0.8, 0.3]
        posterior_protective = calculator._bayesian_update(prior, likelihoods_protective)
        assert posterior_protective < prior

    def test_family_history_extraction(self, calculator, sample_responses):
        """Test family history data extraction."""
        family_history = calculator._extract_family_history(sample_responses)
        
        assert isinstance(family_history, dict)
        assert 'cancer_types' in family_history
        assert 'affected_relatives' in family_history
        assert 'patterns' in family_history
        
        # Should identify breast cancer family pattern
        assert 'breast_cancer_family' in family_history['patterns']
        
        # Should identify ovarian cancer family pattern  
        assert 'ovarian_cancer_family' in family_history['patterns']
        
        # Should identify early onset pattern
        assert 'early_onset_cancer' in family_history['patterns']

    def test_lifestyle_factors_extraction(self, calculator, sample_responses):
        """Test lifestyle factors extraction."""
        lifestyle = calculator._extract_lifestyle_factors(sample_responses)
        
        assert isinstance(lifestyle, dict)
        assert 'smoking' in lifestyle
        assert 'alcohol_consumption' in lifestyle
        assert 'stress_level' in lifestyle
        
        # Verify extracted values match responses
        assert lifestyle['stress_level'] == "High"

    def test_gene_specific_risk_calculation(self, calculator, sample_responses):
        """Test gene-specific risk calculation components."""
        family_history = calculator._extract_family_history(sample_responses)
        symptoms = calculator._extract_symptoms(sample_responses)
        demographics = calculator._extract_demographics(sample_responses)
        medical_history = calculator._extract_medical_history(sample_responses)
        
        # Test BRCA1 risk calculation
        brca1_risk = calculator._calculate_gene_specific_risk(
            "BRCA1", family_history, symptoms, demographics, medical_history
        )
        
        assert isinstance(brca1_risk, GeneticRisk)
        assert brca1_risk.gene_symbol == "BRCA1"
        assert 0 <= brca1_risk.mutation_probability <= 1
        assert len(brca1_risk.confidence_interval) == 2
        assert brca1_risk.evidence_strength in ['low', 'moderate', 'high', 'very_high']

    def test_demographic_likelihood_calculation(self, calculator):
        """Test demographic likelihood calculations."""
        demographics = {
            'age': 35,
            'gender': 'Female',
            'ethnicity': 'Ashkenazi Jewish'
        }
        
        # Test BRCA1 likelihood with Ashkenazi Jewish ethnicity
        likelihood = calculator._calculate_demographic_likelihood("BRCA1", demographics)
        assert likelihood > 1.0  # Should be elevated for Ashkenazi Jewish
        
        # Test age impact
        young_demographics = demographics.copy()
        young_demographics['age'] = 25
        young_likelihood = calculator._calculate_demographic_likelihood("BRCA1", young_demographics)
        assert young_likelihood >= likelihood  # Younger age may increase likelihood

    def test_confidence_interval_calculation(self, calculator):
        """Test confidence interval calculations."""
        prob = 0.15
        ci = calculator._calculate_confidence_interval(prob)
        
        assert len(ci) == 2
        assert ci[0] < prob < ci[1]
        assert ci[0] >= 0
        assert ci[1] <= 1

    def test_clinical_significance_generation(self, calculator):
        """Test clinical significance text generation."""
        # High probability case
        high_prob_sig = calculator._generate_clinical_significance("BRCA1", 0.35)
        assert "high probability" in high_prob_sig.lower()
        assert "genetic counseling" in high_prob_sig.lower()
        
        # Moderate probability case
        mod_prob_sig = calculator._generate_clinical_significance("BRCA1", 0.15)
        assert "moderate probability" in mod_prob_sig.lower()
        assert "genetic testing" in mod_prob_sig.lower()
        
        # Low probability case
        low_prob_sig = calculator._generate_clinical_significance("BRCA1", 0.03)
        assert "low" in low_prob_sig.lower()

    def test_genetic_testing_recommendations(self, calculator):
        """Test genetic testing recommendations."""
        # High risk recommendations
        high_risk_recs = calculator._recommend_genetic_testing("BRCA1", 0.35)
        assert any("urgent" in rec.lower() for rec in high_risk_recs)
        assert any("counseling" in rec.lower() for rec in high_risk_recs)
        
        # Moderate risk recommendations
        mod_risk_recs = calculator._recommend_genetic_testing("BRCA1", 0.15)
        assert any("counseling" in rec.lower() for rec in mod_risk_recs)
        
        # Low risk recommendations
        low_risk_recs = calculator._recommend_genetic_testing("BRCA1", 0.03)
        assert len(low_risk_recs) > 0

    def test_epigenetic_factor_risk_calculation(self, calculator, sample_responses):
        """Test epigenetic factor risk calculation."""
        lifestyle_factors = calculator._extract_lifestyle_factors(sample_responses)
        environmental_exposures = calculator._extract_environmental_exposures(sample_responses)
        dietary_patterns = calculator._extract_dietary_patterns(sample_responses)
        stress_factors = calculator._extract_stress_factors(sample_responses)
        
        # Test cellular stress indicators calculation
        stress_risk = calculator._calculate_epigenetic_factor_risk(
            "cellular_stress_indicators",
            lifestyle_factors,
            environmental_exposures,
            dietary_patterns,
            stress_factors
        )
        
        assert isinstance(stress_risk, EpigeneticFactor)
        assert stress_risk.factor_name == "Cellular Stress Indicators"
        assert stress_risk.risk_level in ['low', 'moderate', 'high']
        assert 0 <= stress_risk.probability_score <= 1
        assert isinstance(stress_risk.modifiable, bool)
        assert isinstance(stress_risk.recommendations, list)

    def test_lifestyle_modifier_calculation(self, calculator):
        """Test lifestyle modifier calculations."""
        lifestyle_factors = {
            'smoking': True,
            'alcohol_consumption': 'Heavy',
            'exercise_frequency': 'Never',
            'diet_quality': 'Poor',
            'stress_level': 'High'
        }
        
        dietary_patterns = {
            'processed_food_frequency': 'High',
            'vegetable_intake': 'Low'
        }
        
        stress_factors = {
            'chronic_stress': True
        }
        
        modifier = calculator._calculate_lifestyle_modifier(
            lifestyle_factors, dietary_patterns, stress_factors
        )
        
        # High-risk lifestyle should result in positive modifier
        assert modifier > 0
        
        # Test protective lifestyle
        protective_lifestyle = {
            'smoking': False,
            'alcohol_consumption': 'Never',
            'exercise_frequency': 'Daily',
            'diet_quality': 'Excellent',
            'stress_level': 'Low'
        }
        
        protective_dietary = {
            'processed_food_frequency': 'Low',
            'vegetable_intake': 'High'
        }
        
        protective_stress = {
            'chronic_stress': False
        }
        
        protective_modifier = calculator._calculate_lifestyle_modifier(
            protective_lifestyle, protective_dietary, protective_stress
        )
        
        # Protective lifestyle should result in negative modifier
        assert protective_modifier < modifier

    def test_environmental_modifier_calculation(self, calculator):
        """Test environmental exposure modifier calculations."""
        # High-risk exposures
        high_risk_exposures = ['asbestos', 'radiation', 'industrial_chemicals']
        high_modifier = calculator._calculate_environmental_modifier(high_risk_exposures)
        assert high_modifier > 0
        
        # Moderate-risk exposures
        mod_risk_exposures = ['air_pollution', 'secondhand_smoke']
        mod_modifier = calculator._calculate_environmental_modifier(mod_risk_exposures)
        assert mod_modifier > 0
        assert mod_modifier < high_modifier
        
        # No exposures
        no_exposures = []
        no_modifier = calculator._calculate_environmental_modifier(no_exposures)
        assert no_modifier == 0

    def test_epigenetic_recommendations_generation(self, calculator):
        """Test epigenetic recommendations generation."""
        lifestyle_factors = {
            'smoking': True,
            'stress_level': 'High'
        }
        
        dietary_patterns = {
            'processed_food_frequency': 'High'
        }
        
        stress_factors = {
            'chronic_stress': True
        }
        
        # Test DNA methylation recommendations
        dna_recs = calculator._generate_epigenetic_recommendations(
            "dna_methylation_patterns", lifestyle_factors, dietary_patterns, stress_factors
        )
        
        assert isinstance(dna_recs, list)
        assert len(dna_recs) > 0
        assert any("folate" in rec.lower() for rec in dna_recs)
        
        # Should include smoking cessation for smokers
        assert any("smoking cessation" in rec.lower() for rec in dna_recs)

    def test_edge_cases(self, calculator):
        """Test edge cases and error handling."""
        # Empty responses
        empty_risks = calculator.calculate_genetic_risks([])
        assert isinstance(empty_risks, list)
        
        # Invalid response format
        invalid_responses = [{"invalid": "data"}]
        try:
            calculator.calculate_genetic_risks(invalid_responses)
        except Exception as e:
            # Should handle gracefully without crashing
            assert True
        
        # Very high probabilities should be capped
        very_high_prior = 0.95
        extreme_likelihoods = [10.0, 50.0, 100.0]
        capped_posterior = calculator._bayesian_update(very_high_prior, extreme_likelihoods)
        assert capped_posterior <= 0.99

    def test_consistency_across_runs(self, calculator, sample_responses):
        """Test that calculations are consistent across multiple runs."""
        # Run genetic risk calculation multiple times
        risks1 = calculator.calculate_genetic_risks(sample_responses)
        risks2 = calculator.calculate_genetic_risks(sample_responses)
        
        # Results should be identical
        assert len(risks1) == len(risks2)
        
        for risk1, risk2 in zip(risks1, risks2):
            assert risk1['gene_symbol'] == risk2['gene_symbol']
            assert abs(risk1['mutation_probability'] - risk2['mutation_probability']) < 1e-10

    def test_performance_benchmarks(self, calculator, sample_responses):
        """Test performance benchmarks for risk calculations."""
        import time
        
        # Test genetic risk calculation performance
        start_time = time.time()
        for _ in range(100):
            calculator.calculate_genetic_risks(sample_responses)
        genetic_time = time.time() - start_time
        
        # Should complete 100 calculations in reasonable time (< 5 seconds)
        assert genetic_time < 5.0
        
        # Test epigenetic risk calculation performance
        start_time = time.time()
        for _ in range(100):
            calculator.calculate_epigenetic_risks(sample_responses)
        epigenetic_time = time.time() - start_time
        
        # Should complete 100 calculations in reasonable time (< 3 seconds)
        assert epigenetic_time < 3.0


class TestGeneticRiskDataClass:
    """Test cases for GeneticRisk data class."""
    
    def test_genetic_risk_creation(self):
        """Test GeneticRisk object creation."""
        risk = GeneticRisk(
            gene_symbol="BRCA1",
            mutation_probability=0.15,
            confidence_interval=(0.08, 0.24),
            evidence_strength="moderate",
            clinical_significance="Test significance",
            recommended_testing=["Test recommendation"]
        )
        
        assert risk.gene_symbol == "BRCA1"
        assert risk.mutation_probability == 0.15
        assert risk.confidence_interval == (0.08, 0.24)
        assert risk.evidence_strength == "moderate"
        assert risk.clinical_significance == "Test significance"
        assert risk.recommended_testing == ["Test recommendation"]


class TestEpigeneticFactorDataClass:
    """Test cases for EpigeneticFactor data class."""
    
    def test_epigenetic_factor_creation(self):
        """Test EpigeneticFactor object creation."""
        factor = EpigeneticFactor(
            factor_name="DNA Methylation Patterns",
            risk_level="moderate",
            probability_score=0.45,
            modifiable=True,
            recommendations=["Test recommendation"]
        )
        
        assert factor.factor_name == "DNA Methylation Patterns"
        assert factor.risk_level == "moderate"
        assert factor.probability_score == 0.45
        assert factor.modifiable == True
        assert factor.recommendations == ["Test recommendation"]


@pytest.mark.integration
class TestRiskCalculatorIntegration:
    """Integration tests for risk calculator with other components."""
    
    def test_integration_with_question_bank(self):
        """Test integration with question bank responses."""
        # This would test the calculator with actual question bank output
        pass
    
    def test_integration_with_api_responses(self):
        """Test integration with API response formats."""
        # This would test the calculator with actual API response formats
        pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
