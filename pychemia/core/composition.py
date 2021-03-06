"""
Class Composition
"""

__author__ = 'Guillermo Avendano-Franco'

from numpy import array, argsort
from fractions import gcd as _gcd
from math import pi

from pychemia.utils.periodic import atomic_symbols, electronegativity, atomic_number, covalent_radius


class Composition():
    """
    The class Composition is basically a dictionary with species as keys and
    number of atoms of that specie as values. The methods provided for Composition objects should
    not contain geometrical information or graph connectivity.

    The main purpose of this class is to be able to parse formulas into compositions and return
    string formulas sorted in various ways.
    """

    def __init__(self, value=None):
        """
        Creates a new composition, internally it is a dictionary
        where each specie is the key and the value is an integer
        with the number of atoms of that specie

        :param value: (str, dict) The value could be a string with a chemical formula or the actual dictionary
        of species and values

        :rtype: Composition
        """

        if isinstance(value, basestring):
            self._set_composition(self.formula_parser(value))
        elif isinstance(value, dict):
            self._set_composition(value)
        else:
            self._composition = {}

    def __len__(self):
        return len(self._composition)

    def _set_composition(self, value):
        """
        Checks the values of a dictionary before seting the actual composition

        :param value: (dict)
        :rtype: None
        """
        for i in value:
            assert(i in atomic_symbols)
            assert(isinstance(value[i], int))
        self._composition = value.copy()

    @property
    def composition(self):
        """
        :return: The composition dictionary

        :rtype: dict
        """
        return self._composition

    @property
    def formula(self):
        """
        :return: The chemical formula with atoms sorted alphabetically

        :rtype: str
        """
        return self.sorted_formula(sortby='alpha', reduced=True)

    @staticmethod
    def formula_parser(value):
        """
        :return: Convert an string representing a chemical formula into a dictionary with the species as keys
                 and values as the number of atoms of that specie

        :param value: (str) String representing a chemical formula

        :rtype: dict
        """
        ret = {}
        jump = False
        for i in range(len(value)):
            if jump > 0:  # This char belongs to the current atom, move on
                jump -= 1
            elif value[i].isupper():  # Atom Name starts with Uppercase
                if i+1 < len(value) and value[i+1].islower():  # Atom name has more than 1 char
                    if i+2 < len(value) and value[i+2].islower():  # Atom name has more than 2 chars
                        specie = value[i:i+3]
                        jump = 2
                    else:
                        specie = value[i:i+2]
                        jump = 1
                else:
                    specie = value[i]
                    jump = 0
                j = 1
                number = ''
                while True:
                    if i+jump+j < len(value) and value[i+jump+j].isdigit():
                        number += value[i+jump+j]
                        j += 1
                    else:
                        break
                if number == '':
                    ret[specie] = 1
                else:
                    ret[specie] = int(number)
        return ret

    @staticmethod
    def explode_composition(formula, units=1):
        import re

        # decompose composition
        a = re.findall(r"[A-Z][a-z0-9]*", formula)
        composition = []
        for i in a:
            m = re.match(r"([A-Za-z]+)([0-9]*)", i)
            if m.group(2) == "":
                n = int(1)
            else:
                n = int(m.group(2))

            for j in range(n*units):
                composition.append(m.group(1))

        return composition

    @property
    def gcd(self):
        """
        :return: The greatest common denominator for the composition

        :rtype: int
        """
        if self.natom > 0:
            return reduce(_gcd, self.values)
        else:
            return 1

    @property
    def symbols(self):
        ret = []
        for specie in self:
            number_atoms_specie = self.composition[specie]
            for i in range(number_atoms_specie):
                ret.append(specie)
        return ret

    @property
    def species(self):
        """
        :return: The list of species

        :rtype: list
        """
        return self._composition.keys()

    @property
    def values(self):
        """
        :return: The number of atoms of each specie

        :rtype: list
        """
        return [self._composition[x] for x in self._composition]

    @property
    def natom(self):
        """
        :return: The number of atoms in the composition

        :rtype: int
        """
        return sum(self.values)

    def sorted_formula(self, sortby='alpha', reduced=True):
        """
        :return: The chemical formula. It could be sorted  alphabetically using sortby='alpha', by electronegativity
                 using sortby='electroneg' or using Hill System with sortby='Hill'

        :param sortby: (str) 'alpha' : Alphabetically
                             'electroneg' : Electronegativity
                             'hill' : Hill System

        :param reduced: (bool) If the formula should be normalized

        :rtype: str
        """
        if reduced and self.gcd > 1:
            comp = Composition(self.composition)
            for i in comp.composition:
                comp._composition[i] /= self.gcd
        else:
            comp = self
        ret = ''
        if sortby == 'electroneg':
            electroneg = electronegativity(comp.species)
            for i in range(len(electroneg)):
                if electroneg[i] is None:
                    electroneg[i] = -1
            sortedspecies = array(comp.species)[argsort(electroneg)]
        elif sortby == "hill":  # FIXME: Hill system exceptions not implemented
            sortedspecies = []
            presortedspecies = sorted(comp.species)
            if 'C' in presortedspecies:
                sortedspecies.append('C')
                presortedspecies.pop(presortedspecies.index('C'))
            if 'H' in presortedspecies:
                sortedspecies.append('H')
                presortedspecies.pop(presortedspecies.index('H'))
            sortedspecies += presortedspecies
        else:
            sortedspecies = sorted(comp.species)
        for specie in sortedspecies:
            ret += specie
            if comp.composition[specie] > 1:
                ret += str(comp.composition[specie])
        return ret

    def species_bin(self):
        spec_bin = 0L
        for i in atomic_number(self.species):
            spec_bin += 2**i
        return spec_bin

    def species_hex(self):
        spec_hex = 0L
        i = 0
        for atom_number in sorted(atomic_number(self.species)):
            spec_hex += atom_number*(256**i)
            i += 1
        return spec_hex

    def __repr__(self):
        return 'Composition('+str(self.composition)+')'

    def __str__(self):
        ret = ''
        for i in self.species:
            ret += " %3s: %4d  " % (i, self.composition[i])
        return ret

    def __iter__(self):
        return iter(self.composition)

    def covalent_volume(self, packing='cubes'):

        if packing == 'cubes':
            factor = 8
        elif packing == 'spheres':
            factor = 4 * pi / 3.0
        else:
            raise ValueError('Non-valid packing value ', packing)

        # find volume of unit cell by adding cubes
        volume = 0.0
        for specie in self:
            number_atoms_specie = self.composition[specie]
            # Pack each atom in a cube (2*r)^3
            volume += factor*number_atoms_specie*covalent_radius(specie)**3
        return volume
