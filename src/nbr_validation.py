"""
Validação de cálculos conforme normas brasileiras
NBR 6122 (2019) - Projeto e execução de fundações
NBR 6118 (2014) - Projeto de estruturas de concreto
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

class FoundationType(Enum):
    """Tipos de fundação conforme NBR 6122"""
    SAPATA_ISOLADA = "sapata_isolada"
    SAPATA_CORRIDA = "sapata_corrida"
    SAPATA_ASSOCIADA = "sapata_associada"
    SAPATA_ALUNADA = "sapata_alunada"
    BLOCO = "bloco"
    ESTACA_PRANCHA = "estaca_prancha"
    ESTACA_HÉLICE = "estaca_helice"
    ESTACA_RAIZ = "estaca_raiz"
    ESTACA_MEGAPERFIL = "estaca_megaperfil"
    TUBULAO = "tubulao"

class SoilClass(Enum):
    """Classificação de solos conforme NBR 6484"""
    ARGILA_MOLE = "argila_mole"
    ARGILA_RIJA = "argila_rija"
    SILTE = "silte"
    AREIA_FINA = "areia_fina"
    AREIA_MEDIA = "areia_media"
    AREIA_GROSSA = "areia_grossa"
    PEDREGULHO = "pedregulho"
    ROCHA_SEDIMENTAR = "rocha_sedimentar"
    ROCHA_IGNEA = "rocha_igneo"

@dataclass
class NBR6122_Requirements:
    """Requisitos mínimos da NBR 6122:2019"""
    
    # Fatores de segurança mínimos (Tabela 1 - NBR 6122)
    MIN_SAFETY_FACTORS = {
        'combinação_normal': 2.0,
        'combinação_especial': 1.8,
        'combinação_excepcional': 1.6
    }
    
    # Recalques admissíveis (Tabela 2 - NBR 6122)
    MAX_SETTLEMENTS = {
        'edificios_comuns': 0.025,  # 25 mm
        'edificios_altos': 0.015,   # 15 mm
        'pontes_viadutos': 0.010,   # 10 mm
        'tanques_silos': 0.020      # 20 mm
    }
    
    # Dimensões mínimas (item 6.3.2)
    MIN_DIMENSIONS = {
        'sapata_largura_min': 0.60,    # 60 cm
        'sapata_altura_min': 0.40,     # 40 cm
        'estaca_diametro_min': 0.25,   # 25 cm
        'bloco_altura_min': 0.60,      # 60 cm
    }
    
    # Cobrimentos mínimos (compatível com NBR 6118)
    MIN_COVER = {
        'fundacao_enterrada': 0.05,    # 5 cm
        'fundacao_agressivo': 0.075,   # 7.5 cm
        'fundacao_marinha': 0.10       # 10 cm
    }

class NBR6122_Validator:
    """Validador de projetos de fundação conforme NBR 6122"""
    
    def __init__(self, soil_class: SoilClass, water_table_depth: float = 5.0):
        self.soil_class = soil_class
        self.water_table_depth = water_table_depth
        self.requirements = NBR6122_Requirements()
        
    def validate_bearing_capacity(self, q_ult: float, q_applied: float, 
                                load_combination: str = 'combinação_normal') -> dict:
        """
        Valida capacidade de carga conforme NBR 6122
        
        Args:
            q_ult: Capacidade última (kPa)
            q_applied: Tensão aplicada (kPa)
            load_combination: Tipo de combinação de carga
            
        Returns:
            dict: Resultados da validação
        """
        # Fator de segurança calculado
        FS_calculated = q_ult / q_applied if q_applied > 0 else float('inf')
        
        # Fator de segurança mínimo da norma
        FS_min_required = self.requirements.MIN_SAFETY_FACTORS[load_combination]
        
        # Verificação
        is_valid = FS_calculated >= FS_min_required
        
        # Coeficiente de utilização
        utilization_ratio = FS_min_required / FS_calculated if FS_calculated > 0 else 0
        
        return {
            'is_valid': is_valid,
            'FS_calculated': FS_calculated,
            'FS_min_required': FS_min_required,
            'utilization_ratio': utilization_ratio,
            'status': '✅ ATENDE' if is_valid else '❌ NÃO ATENDE',
            'norm_reference': 'NBR 6122:2019 - Tabela 1'
        }
    
    def validate_settlement(self, settlement: float, structure_type: str) -> dict:
        """
        Valida recalques conforme limites da NBR 6122
        
        Args:
            settlement: Recalque calculado (m)
            structure_type: Tipo de estrutura
            
        Returns:
            dict: Resultados da validação
        """
        settlement_mm = settlement * 1000
        
        # Limite máximo conforme tipo de estrutura
        max_settlement_mm = self.requirements.MAX_SETTLEMENTS[structure_type] * 1000
        
        # Verificação
        is_valid = settlement_mm <= max_settlement_mm
        
        # Margem disponível
        margin_mm = max_settlement_mm - settlement_mm
        
        return {
            'is_valid': is_valid,
            'settlement_mm': settlement_mm,
            'max_allowed_mm': max_settlement_mm,
            'margin_mm': margin_mm,
            'status': '✅ ATENDE' if is_valid else '❌ NÃO ATENDE',
            'norm_reference': 'NBR 6122:2019 - Tabela 2'
        }
    
    def validate_foundation_dimensions(self, foundation_type: FoundationType,
                                     width: float, length: float, 
                                     height: float = None) -> dict:
        """
        Valida dimensões mínimas conforme NBR 6122
        
        Args:
            foundation_type: Tipo de fundação
            width: Largura (m)
            length: Comprimento (m)
            height: Altura (m) - opcional
            
        Returns:
            dict: Resultados da validação
        """
        violations = []
        
        # Verificar largura mínima
        if width < self.requirements.MIN_DIMENSIONS['sapata_largura_min']:
            violations.append(f"Largura mínima: {self.requirements.MIN_DIMENSIONS['sapata_largura_min']*100} cm")
        
        # Verificar altura mínima se for sapata/bloco
        if height is not None:
            if foundation_type.value.startswith('sapata'):
                min_height = self.requirements.MIN_DIMENSIONS['sapata_altura_min']
            elif foundation_type == FoundationType.BLOCO:
                min_height = self.requirements.MIN_DIMENSIONS['bloco_altura_min']
            else:
                min_height = 0
            
            if height < min_height:
                violations.append(f"Altura mínima: {min_height*100} cm")
        
        # Verificar relação comprimento/largura para sapatas
        if foundation_type.value.startswith('sapata'):
            if length / width > 3.0:
                violations.append("Relação L/B máxima: 3.0")
        
        is_valid = len(violations) == 0
        
        return {
            'is_valid': is_valid,
            'violations': violations,
            'status': '✅ ATENDE' if is_valid else f'❌ {len(violations)} violação(ões)',
            'norm_reference': 'NBR 6122:2019 - Item 6.3.2'
        }
    
    def validate_pile_dimensions(self, diameter: float, length: float) -> dict:
        """
        Valida dimensões de estacas conforme NBR 6122
        
        Args:
            diameter: Diâmetro (m)
            length: Comprimento (m)
            
        Returns:
            dict: Resultados da validação
        """
        violations = []
        
        # Diâmetro mínimo
        if diameter < self.requirements.MIN_DIMENSIONS['estaca_diametro_min']:
            violations.append(f"Diâmetro mínimo: {self.requirements.MIN_DIMENSIONS['estaca_diametro_min']*100} cm")
        
        # Comprimento mínimo (5x diâmetro)
        if length < 5 * diameter:
            violations.append(f"Comprimento mínimo: 5× diâmetro = {5*diameter*100:.1f} cm")
        
        # Comprimento máximo prático (30m para estacas cravadas)
        if length > 30.0:
            violations.append("Comprimento máximo prático: 30 m")
        
        is_valid = len(violations) == 0
        
        return {
            'is_valid': is_valid,
            'violations': violations,
            'status': '✅ ATENDE' if is_valid else f'❌ {len(violations)} violação(ões)',
            'norm_reference': 'NBR 6122:2019 - Item 7.2'
        }
    
    def calculate_soil_pressure_limits(self) -> dict:
        """
        Calcula tensões admissíveis no solo conforme NBR 6122
        
        Returns:
            dict: Tensões admissíveis por tipo de solo
        """
        # Tensões admissíveis (kPa) - Valores típicos da norma
        pressure_limits = {
            SoilClass.ARGILA_MOLE: 50,
            SoilClass.ARGILA_RIJA: 200,
            SoilClass.SILTE: 100,
            SoilClass.AREIA_FINA: 150,
            SoilClass.AREIA_MEDIA: 250,
            SoilClass.AREIA_GROSSA: 400,
            SoilClass.PEDREGULHO: 600,
            SoilClass.ROCHA_SEDIMENTAR: 1000,
            SoilClass.ROCHA_IGNEA: 2000
        }
        
        return {
            'soil_class': self.soil_class.value,
            'admissible_pressure_kPa': pressure_limits.get(self.soil_class, 100),
            'norm_reference': 'NBR 6122:2019 - Anexo A'
        }
    
    def validate_water_table_effect(self, foundation_depth: float) -> dict:
        """
        Valida efeito do lençol freático conforme NBR 6122
        
        Args:
            foundation_depth: Profundidade da fundação (m)
            
        Returns:
            dict: Análise do lençol freático
        """
        # Verificar se a fundação está abaixo do lençol
        below_water_table = foundation_depth > self.water_table_depth
        
        # Recomendações da norma
        if below_water_table:
            recommendation = (
                "Fundação abaixo do lençol freático. Considerar: "
                "1) Peso específico submerso para cálculo de tensões efetivas\n"
                "2) Possibilidade de tubulação para rebaixamento\n"
                "3) Verificação de piping em solos arenosos"
            )
            risk_level = "ALTO"
        else:
            recommendation = (
                "Fundação acima do lençol freático. "
                "Condições favoráveis para execução."
            )
            risk_level = "BAIXO"
        
        return {
            'below_water_table': below_water_table,
            'foundation_depth': foundation_depth,
            'water_table_depth': self.water_table_depth,
            'recommendation': recommendation,
            'risk_level': risk_level,
            'norm_reference': 'NBR 6122:2019 - Item 4.2.3'
        }
    
    def generate_nbr_compliance_report(self, validation_results: List[dict]) -> str:
        """
        Gera relatório de conformidade com NBR 6122
        
        Args:
            validation_results: Lista de resultados de validação
            
        Returns:
            str: Relatório formatado
        """
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("RELATÓRIO DE CONFORMIDADE - NBR 6122:2019")
        report_lines.append("=" * 70)
        report_lines.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        report_lines.append(f"Classe de solo: {self.soil_class.value}")
        report_lines.append("")
        
        # Contadores
        total_tests = len(validation_results)
        passed_tests = sum(1 for r in validation_results if r.get('is_valid', False))
        
        # Resumo
        report_lines.append("📊 RESUMO DA VALIDAÇÃO")
        report_lines.append(f"  Testes realizados: {total_tests}")
        report_lines.append(f"  Testes aprovados: {passed_tests}")
        report_lines.append(f"  Conformidade: {passed_tests/total_tests*100:.1f}%")
        report_lines.append("")
        
        # Detalhamento
        report_lines.append("🔍 DETALHAMENTO POR ITEM")
        for i, result in enumerate(validation_results, 1):
            report_lines.append(f"\n{i}. {result.get('test_name', f'Teste {i}')}")
            report_lines.append(f"   Status: {result.get('status', 'N/A')}")
            report_lines.append(f"   Referência: {result.get('norm_reference', 'N/A')}")
            
            if 'violations' in result and result['violations']:
                report_lines.append("   Violações:")
                for violation in result['violations']:
                    report_lines.append(f"     - {violation}")
            
            if 'recommendation' in result:
                report_lines.append(f"   Recomendação: {result['recommendation']}")
        
        # Conclusão
        report_lines.append("\n" + "=" * 70)
        report_lines.append("CONCLUSÃO")
        
        if passed_tests == total_tests:
            report_lines.append("✅ PROJETO CONFORME COM A NBR 6122:2019")
            report_lines.append("   Todas as verificações atendem aos requisitos normativos.")
        else:
            report_lines.append("⚠️  ATENÇÃO: VERIFICAÇÕES PENDENTES")
            report_lines.append("   Revise os itens indicados acima.")
        
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)

class NBR6118_ConcreteValidator:
    """Validador para concreto armado conforme NBR 6118:2014"""
    
    def __init__(self, fck: float = 25, aggressiveness_class: str = 'I'):
        """
        Args:
            fck: Resistência característica do concreto (MPa)
            aggressiveness_class: Classe de agressividade (I, II, III, IV)
        """
        self.fck = fck
        self.aggressiveness_class = aggressiveness_class
        
    def validate_concrete_strength(self, required_strength: float) -> dict:
        """
        Valida resistência do concreto conforme NBR 6118
        
        Args:
            required_strength: Resistência necessária (MPa)
            
        Returns:
            dict: Resultados da validação
        """
        # Fator de minoração γc = 1.4 (concreto)
        design_strength = self.fck / 1.4
        
        is_valid = design_strength >= required_strength
        
        return {
            'is_valid': is_valid,
            'fck': self.fck,
            'fcd': design_strength,
            'required_fcd': required_strength,
            'safety_margin': design_strength - required_strength,
            'status': '✅ ATENDE' if is_valid else '❌ NÃO ATENDE',
            'norm_reference': 'NBR 6118:2014 - Item 12.3.3'
        }
    
    def calculate_minimum_reinforcement(self, cross_section_area: float) -> dict:
        """
        Calcula armadura mínima conforme NBR 6118
        
        Args:
            cross_section_area: Área da seção transversal (cm²)
            
        Returns:
            dict: Armaduras mínimas
        """
        # Taxas mínimas de armadura (Tabela 17.3 - NBR 6118)
        min_reinforcement_ratios = {
            'flexao': 0.15,  # 0,15% para flexão
            'tracao': 0.50,  # 0,50% para tração
            'compressao': 0.40  # 0,40% para compressão
        }
        
        # Área de aço mínima (cm²)
        As_min = {
            'flexao': min_reinforcement_ratios['flexao'] / 100 * cross_section_area,
            'tracao': min_reinforcement_ratios['tracao'] / 100 * cross_section_area,
            'compressao': min_reinforcement_ratios['compressao'] / 100 * cross_section_area
        }
        
        # Diâmetro mínimo das barras (mm)
        min_bar_diameter = {
            'pilares': 10,
            'vigas': 8,
            'lajes': 5
        }
        
        return {
            'cross_section_area_cm2': cross_section_area,
            'As_min_flexao_cm2': As_min['flexao'],
            'As_min_tracao_cm2': As_min['tracao'],
            'As_min_compressao_cm2': As_min['compressao'],
            'min_bar_diameter_mm': min_bar_diameter,
            'norm_reference': 'NBR 6118:2014 - Tabela 17.3'
        }
    
    def validate_cover_thickness(self, element_type: str, 
                               proposed_cover: float) -> dict:
        """
        Valida cobrimento conforme agressividade
        
        Args:
            element_type: Tipo de elemento (fundacao, viga, pilar)
            proposed_cover: Cobrimento proposto (cm)
            
        Returns:
            dict: Validação do cobrimento
        """
        # Cobrimentos mínimos (cm) - Tabela 7.2 - NBR 6118
        min_covers = {
            'I': {'fundacao': 3.0, 'viga': 2.5, 'pilar': 2.5},
            'II': {'fundacao': 4.0, 'viga': 3.0, 'pilar': 3.0},
            'III': {'fundacao': 5.0, 'viga': 4.0, 'pilar': 4.0},
            'IV': {'fundacao': 5.0, 'viga': 4.5, 'pilar': 4.5}
        }
        
        min_required = min_covers[self.aggressiveness_class][element_type]
        is_valid = proposed_cover >= min_required
        
        return {
            'is_valid': is_valid,
            'proposed_cover': proposed_cover,
            'min_required': min_required,
            'aggressiveness_class': self.aggressiveness_class,
            'status': '✅ ATENDE' if is_valid else '❌ NÃO ATENDE',
            'norm_reference': 'NBR 6118:2014 - Tabela 7.2'
        }

# Exemplo de uso integrado no Streamlit
def nbr_validation_ui():
    """Interface de validação NBR para Streamlit"""
    import streamlit as st
    
    st.subheader("📐 Validação conforme Normas Brasileiras")
    
    tab1, tab2 = st.tabs(["NBR 6122 - Fundações", "NBR 6118 - Concreto"])
    
    with tab1:
        st.markdown("### NBR 6122:2019 - Projeto e Execução de Fundações")
        
        # Seleção de solo
        soil_options = {s.value: s for s in SoilClass}
        selected_soil = st.selectbox(
            "Classificação do solo:",
            options=list(soil_options.keys()),
            index=2
        )
        
        water_table = st.number_input(
            "Profundidade do lençol freático (m):",
            0.0, 20.0, 2.0, 0.5
        )
        
        validator = NBR6122_Validator(
            soil_class=soil_options[selected_soil],
            water_table_depth=water_table
        )
        
        # Validações
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Capacidade de Carga**")
            q_ult = st.number_input("q_ult (kPa):", 100, 5000, 800, 10)
            q_app = st.number_input("q_aplicada (kPa):", 50, 2000, 200, 10)
            
            if st.button("Validar Capacidade"):
                result = validator.validate_bearing_capacity(q_ult, q_app)
                
                st.metric("FS Calculado", f"{result['FS_calculated']:.2f}")
                st.metric("FS Mínimo NBR", f"{result['FS_min_required']:.2f}")
                
                if result['is_valid']:
                    st.success(result['status'])
                else:
                    st.error(result['status'])
        
        with col2:
            st.markdown("**Dimensões de Sapata**")
            width = st.number_input("Largura (m):", 0.3, 5.0, 1.0, 0.1)
            length = st.number_input("Comprimento (m):", 0.3, 5.0, 1.5, 0.1)
            height = st.number_input("Altura (m):", 0.2, 2.0, 0.5, 0.1)
            
            if st.button("Validar Dimensões"):
                result = validator.validate_foundation_dimensions(
                    FoundationType.SAPATA_ISOLADA, width, length, height
                )
                
                if result['is_valid']:
                    st.success(result['status'])
                else:
                    st.error(result['status'])
                    st.write("Violações:")
                    for violation in result['violations']:
                        st.write(f"- {violation}")
        
        # Tensão admissível do solo
        st.markdown("### Tensão Admissível do Solo")
        pressure_limits = validator.calculate_soil_pressure_limits()
        
        st.metric(
            "Tensão Admissível", 
            f"{pressure_limits['admissible_pressure_kPa']} kPa",
            help="Valor típico conforme NBR 6122 - Anexo A"
        )
        
        # Relatório completo
        if st.button("📄 Gerar Relatório NBR 6122", type="primary"):
            # Coletar todas as validações
            validations = []
            
            # Exemplo de validações
            validations.append({
                'test_name': 'Capacidade de carga',
                **validator.validate_bearing_capacity(q_ult, q_app)
            })
            
            validations.append({
                'test_name': 'Dimensões da fundação',
                **validator.validate_foundation_dimensions(
                    FoundationType.SAPATA_ISOLADA, width, length, height
                )
            })
            
            # Gerar relatório
            report = validator.generate_nbr_compliance_report(validations)
            
            # Exibir relatório
            with st.expander("📋 Ver Relatório Completo"):
                st.text(report)
            
            # Opção de download
            st.download_button(
                label="📥 Baixar Relatório",
                data=report,
                file_name=f"relatorio_nbr6122_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    with tab2:
        st.markdown("### NBR 6118:2014 - Projeto de Estruturas de Concreto")
        
        # Parâmetros do concreto
        fck = st.select_slider(
            "fck do concreto (MPa):",
            options=[20, 25, 30, 35, 40, 50],
            value=25
        )
        
        aggressiveness = st.selectbox(
            "Classe de agressividade ambiental:",
            options=['I', 'II', 'III', 'IV'],
            index=0,
            help="I: Fraca, II: Moderada, III: Forte, IV: Muito Forte"
        )
        
        concrete_validator = NBR6118_ConcreteValidator(fck, aggressiveness)
        
        # Validações
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Resistência do Concreto**")
            required_fcd = st.number_input("fcd necessário (MPa):", 10, 40, 15, 1)
            
            if st.button("Validar fck"):
                result = concrete_validator.validate_concrete_strength(required_fcd)
                
                st.metric("fcd disponível", f"{result['fcd']:.1f} MPa")
                st.metric("fcd necessário", f"{result['required_fcd']:.1f} MPa")
                
                if result['is_valid']:
                    st.success(result['status'])
                else:
                    st.error(result['status'])
        
        with col2:
            st.markdown("**Cobrimento**")
            element_type = st.selectbox(
                "Tipo de elemento:",
                options=['fundacao', 'viga', 'pilar']
            )
            
            proposed_cover = st.number_input(
                "Cobrimento proposto (cm):",
                2.0, 10.0, 3.0, 0.5
            )
            
            if st.button("Validar Cobrimento"):
                result = concrete_validator.validate_cover_thickness(
                    element_type, proposed_cover
                )
                
                st.metric("Cobrimento mínimo", f"{result['min_required']} cm")
                st.metric("Cobrimento proposto", f"{proposed_cover} cm")
                
                if result['is_valid']:
                    st.success(result['status'])
                else:
                    st.error(result['status'])

if __name__ == "__main__":
    # Teste das validações
    print("=== TESTE NBR 6122 ===")
    
    validator = NBR6122_Validator(
        soil_class=SoilClass.AREIA_MEDIA,
        water_table_depth=2.0
    )
    
    # Teste capacidade de carga
    result = validator.validate_bearing_capacity(800, 250)
    print(f"Capacidade de carga: {result}")
    
    # Teste dimensões
    result = validator.validate_foundation_dimensions(
        FoundationType.SAPATA_ISOLADA, 0.5, 1.5, 0.3
    )
    print(f"Dimensões: {result}")
    
    # Teste tensão admissível
    result = validator.calculate_soil_pressure_limits()
    print(f"Tensão admissível: {result}")
    
    print("\n=== TESTE NBR 6118 ===")
    
    concrete_validator = NBR6118_ConcreteValidator(fck=25, aggressiveness_class='II')
    
    # Teste resistência
    result = concrete_validator.validate_concrete_strength(15)
    print(f"Resistência concreto: {result}")
    
    # Teste armadura mínima
    result = concrete_validator.calculate_minimum_reinforcement(1000)
    print(f"Armadura mínima: {result}")