"""
Module d'implémentation de la méthode AHP (Analytic Hierarchy Process / Saaty 1980).
Permet de dériver des poids de critères rigoureux avec calcul de consistance mathématique.
"""

from typing import Dict, List, Tuple, Union
import numpy as np


class AHPModel:
    """
    Modèle d'aide à la décision multicritère AHP de Thomas Saaty.
    """

    # Table des indices aléatoires (Random Consistency Index - RI) de Saaty
    RANDOM_INDEX: Dict[int, float] = {
        1: 0.00,
        2: 0.00,
        3: 0.58,
        4: 0.90,
        5: 1.12,
        6: 1.24,
        7: 1.32,
        8: 1.41,
        9: 1.45,
        10: 1.49,
    }

    def __init__(
        self,
        criteria: List[str],
        pairwise_matrix: Union[List[List[float]], np.ndarray],
    ):
        """
        Initialise le modèle AHP avec les critères et la matrice de comparaison.

        :param criteria: Liste des noms des critères (ex: ['geology', 'rainfall', 'slope', 'tpi'])
        :param pairwise_matrix: Matrice carrée nxn réciproque (A[i,j] = 1 / A[j,i], A[i,i] = 1)
        """
        self.criteria = list(criteria)
        self.n = len(self.criteria)
        self.matrix = np.array(pairwise_matrix, dtype=float)

        if self.matrix.shape != (self.n, self.n):
            raise ValueError(
                f"La matrice doit être de dimension ({self.n}, {self.n}), "
                f"mais a la forme {self.matrix.shape}."
            )

        self._validate_reciprocal()
        self.weights: Dict[str, float] = {}
        self.lambda_max: float = 0.0
        self.ci: float = 0.0
        self.cr: float = 0.0
        self.is_consistent: bool = False

        self._compute_weights_and_consistency()

    def _validate_reciprocal(self) -> None:
        """Vérifie la réciprocité de la matrice (A[i,j] * A[j,i] ~= 1 et diagonale == 1)."""
        for i in range(self.n):
            if not np.isclose(self.matrix[i, i], 1.0, atol=1e-4):
                raise ValueError(f"L'élément diagonal ({i},{i}) doit être égal à 1.")
            for j in range(i + 1, self.n):
                prod = self.matrix[i, j] * self.matrix[j, i]
                if not np.isclose(prod, 1.0, atol=1e-3):
                    raise ValueError(
                        f"La matrice n'est pas réciproque en ({i},{j}) : "
                        f"A[{i},{j}] = {self.matrix[i, j]} et A[{j},{i}] = {self.matrix[j, i]}."
                    )

    def _compute_weights_and_consistency(self) -> None:
        """Calcule les poids par la méthode du vecteur propre principal et le ratio CR."""
        # Calcul des valeurs et vecteurs propres
        eigenvalues, eigenvectors = np.linalg.eig(self.matrix)

        # La plus grande valeur propre réelle (Perron-Frobenius)
        max_idx = np.argmax(np.real(eigenvalues))
        self.lambda_max = float(np.real(eigenvalues[max_idx]))

        # Vecteur propre correspondant, normalisé
        principal_vector = np.real(eigenvectors[:, max_idx])
        normalized_weights = principal_vector / np.sum(principal_vector)

        # Stocker les poids par critère
        self.weights = {
            name: float(w) for name, w in zip(self.criteria, normalized_weights)
        }

        # Calcul de l'indice de cohérence (CI) et ratio de cohérence (CR)
        if self.n <= 2:
            self.ci = 0.0
            self.cr = 0.0
            self.is_consistent = True
        else:
            self.ci = float((self.lambda_max - self.n) / (self.n - 1))
            ri = self.RANDOM_INDEX.get(self.n, 1.49)
            self.cr = float(self.ci / ri) if ri > 0 else 0.0
            self.is_consistent = self.cr < 0.10

    def get_weights(self) -> Dict[str, float]:
        """Retourne le dictionnaire des poids normalisés."""
        return self.weights

    def summary(self) -> str:
        """Génère un résumé textuel détaillé de l'analyse AHP."""
        lines = [
            "=" * 60,
            " ANALYSE AHP DE SAATY (ANALYTIC HIERARCHY PROCESS)",
            "=" * 60,
            f" Nombre de critères (n) : {self.n}",
            f" Valeur propre max (λmax) : {self.lambda_max:.4f}",
            f" Indice de consistance (CI) : {self.ci:.4f}",
            f" Ratio de consistance (CR)  : {self.cr:.4f} "
            f"({'✅ Cohérent (< 0.10)' if self.is_consistent else '❌ Incohérent (>= 0.10)'})",
            "-" * 60,
            " Poids finaux calculés :",
        ]
        for name, w in self.weights.items():
            lines.append(f"   • {name:<15} : {w:.4f} ({w * 100:.1f}%)")
        lines.append("=" * 60)
        return "\n".join(lines)


def calculate_ahp_weights(
    criteria: List[str], pairwise_matrix: Union[List[List[float]], np.ndarray]
) -> Tuple[Dict[str, float], float, bool]:
    """
    Fonction helper rapide pour calculer les poids AHP.

    :returns: Tuple (poids, CR, est_cohérent)
    """
    model = AHPModel(criteria, pairwise_matrix)
    return model.get_weights(), model.cr, model.is_consistent
