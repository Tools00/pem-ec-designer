"""Physical constants — CODATA 2018 recommended values.

@ref: CODATA 2018, Mohr et al. 2019, Rev. Mod. Phys. 84, 1527.
@ref: NIST CODATA Reference, https://physics.nist.gov/cuu/Constants/

All values in SI units. Do not round. Do not change without ADR.
"""

CODATA_VERSION: str = "2018"

# Faraday constant — coulombs per mole
FARADAY: float = 96_485.332_12  # C/mol

# Gas constant — joules per mole per kelvin
GAS_CONSTANT: float = 8.314_462_618  # J/(mol·K)

# Electron charge — coulombs
ELECTRON_CHARGE: float = 1.602_176_634e-19  # C (exact, 2019 SI redefinition)

# Avogadro constant — per mole
AVOGADRO: float = 6.022_140_76e23  # 1/mol (exact, 2019 SI redefinition)

# Standard reference state (IUPAC 1982)
STANDARD_TEMPERATURE: float = 298.15  # K (25 °C)
STANDARD_PRESSURE: float = 100_000.0  # Pa (1 bar)

# Hydrogen molar mass — IUPAC 2021 atomic weight
MOLAR_MASS_H2: float = 2.015_88e-3  # kg/mol

# Higher and Lower heating value of H2 (NIST)
HHV_H2: float = 285_830.0  # J/mol — at 25 °C, liquid water product
LHV_H2: float = 241_820.0  # J/mol — at 25 °C, water vapour product

# Reversible cell potential at standard state for water electrolysis
# U_rev = ΔG / (n·F) with n=2, ΔG_H2O(l) = -237.13 kJ/mol → U_rev ≈ 1.229 V
REVERSIBLE_VOLTAGE_25C: float = 1.229  # V (liquid water reactant)

# Thermoneutral voltage U_tn = ΔH / (n·F) → ≈ 1.481 V
THERMONEUTRAL_VOLTAGE_25C: float = 1.481  # V
