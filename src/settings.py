"""
Configurações centralizadas do projeto SimulaSolo
Versão 1.0
"""
from typing import Dict, Any
from enum import Enum

class SistemaUnidades(Enum):
    """Sistemas de unidades suportados"""
    SI = "SI"           # kN, m, kPa
    MKS = "MKS"         # kgf, m, kgf/cm²
    INGLES = "INGLES"   # lb, ft, psi

class Configuracao:
    """Classe de configuração centralizada"""
    
    # Unidades padrão
    UNIDADE_PADRAO = SistemaUnidades.SI
    
    # Fatores de conversão
    CONVERSOES = {
        SistemaUnidades.SI: {
            'forca': 1.0,           # kN
            'comprimento': 1.0,     # m
            'pressao': 1.0,         # kPa
            'peso_especifico': 1.0  # kN/m³
        },
        SistemaUnidades.MKS: {
            'forca': 0.101971621,   # kN para tf
            'comprimento': 1.0,     # m
            'pressao': 0.0101972,   # kPa para kgf/cm²
            'peso_especifico': 0.101971621  # kN/m³ para tf/m³
        },
        SistemaUnidades.INGLES: {
            'forca': 0.224809,      # kN para kip
            'comprimento': 3.28084, # m para ft
            'pressao': 0.145038,    # kPa para psi
            'peso_especifico': 6.36588  # kN/m³ para pcf
        }
    }
    
    # Fatores de segurança recomendados
    FATORES_SEGURANCA = {
        'fundacoes_rasas': 3.0,
        'fundacoes_profundas': 2.0,
        'comb_normal': 2.0,
        'comb_especial': 1.8,
        'comb_excepcional': 1.6
    }
    
    # Limites de recalque (mm)
    LIMITES_RECALQUE = {
        'edificios_comuns': 25.0,
        'edificios_altos': 15.0,
        'pontes': 10.0,
        'tanques': 20.0
    }
    
    # Dimensões mínimas (m)
    DIMENSOES_MINIMAS = {
        'sapata_largura': 0.6,
        'sapata_altura': 0.4,
        'estaca_diametro': 0.25,
        'bloco_altura': 0.6
    }
    
    @classmethod
    def converter_unidade(cls, valor: float, tipo: str, 
                         de: SistemaUnidades, para: SistemaUnidades) -> float:
        """Converte valor entre sistemas de unidades"""
        if de == para:
            return valor
        
        # Converter para SI primeiro
        if de != SistemaUnidades.SI:
            fator_de = cls.CONVERSOES[de][tipo]
            valor_si = valor / fator_de
        else:
            valor_si = valor
        
        # Converter para sistema destino
        if para != SistemaUnidades.SI:
            fator_para = cls.CONVERSOES[para][tipo]
            return valor_si * fator_para
        else:
            return valor_si
    
    @classmethod
    def formatar_unidade(cls, valor: float, tipo: str, 
                        sistema: SistemaUnidades) -> str:
        """Formata valor com unidade apropriada"""
        unidades = {
            SistemaUnidades.SI: {
                'forca': 'kN',
                'comprimento': 'm',
                'pressao': 'kPa',
                'peso_especifico': 'kN/m³'
            },
            SistemaUnidades.MKS: {
                'forca': 'tf',
                'comprimento': 'm',
                'pressao': 'kgf/cm²',
                'peso_especifico': 'tf/m³'
            },
            SistemaUnidades.INGLES: {
                'forca': 'kip',
                'comprimento': 'ft',
                'pressao': 'psi',
                'peso_especifico': 'pcf'
            }
        }
        
        unidade = unidades[sistema][tipo]
        return f"{valor:.2f} {unidade}"

class Logger:
    """Sistema de logging centralizado"""
    
    @staticmethod
    def info(mensagem: str):
        print(f"[INFO] {mensagem}")
    
    @staticmethod
    def warning(mensagem: str):
        print(f"[WARNING] {mensagem}")
    
    @staticmethod
    def error(mensagem: str):
        print(f"[ERROR] {mensagem}")
    
    @staticmethod
    def debug(mensagem: str):
        print(f"[DEBUG] {mensagem}")
