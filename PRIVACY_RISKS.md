# Analyse des Risques Résiduels de Confidentialité et Nature de la Protection

**Important :** Pulse IA utilise une architecture de **pseudonymisation** avancée et non un anonymat absolu. Bien que l'identité soit techniquement séparée des réponses, un risque résiduel de ré-identification par croisement de données existe toujours dans les systèmes de reporting.

## 1. Risque de Ré-identification par Croisement (Jigsaw Effect)

## 1. Risque de Ré-identification par Croisement (Jigsaw Effect)
**Description** : Un utilisateur disposant d'accès aux rapports pourrait, en croisant plusieurs filtres (ex: Direction RH + Localisation Montréal + Ancienneté > 10 ans), isoler un individu si la population résultante est très faible.
**Mitigation** : Pulse IA impose un seuil minimal d'agrégation (configurable, par défaut n=5). Les résultats ne sont pas affichés si le groupe est trop petit.
**Risque résiduel** : Des combinaisons complexes de segments, bien que dépassant le seuil de 5, pourraient encore permettre des déductions par élimination dans des petites organisations.

## 2. Corrélation Temporelle
**Description** : Si un administrateur surveille en temps réel l'arrivée des réponses anonymes, il pourrait corréler l'heure de soumission avec l'activité connue d'un employé.
**Mitigation** : Pulse IA applique un "jittering" aléatoire (± 12 heures) sur l'horodatage des réponses anonymes stockées en base de données.
**Risque résiduel** : Dans des organisations à très faible volume de réponses, le jittering pourrait ne pas suffire si les réponses sont très espacées dans le temps (ex: une seule réponse par semaine).

## 3. Contenu des Commentaires Ouverts
**Description** : Les répondants peuvent involontairement s'identifier par leur style d'écriture, les faits spécifiques mentionnés ou en signant leur commentaire.
**Mitigation** : Pulse IA applique le seuil de confidentialité aux commentaires. Un message d'avertissement est affiché au répondant avant la soumission.
**Risque résiduel** : Le contenu sémantique lui-même reste un vecteur d'identification que seule une revue humaine ou une IA de désidentification avancée pourrait totalement neutraliser.

## 4. Accès Administrateur Base de Données
**Description** : Un administrateur système disposant d'un accès direct à la base de données pourrait tenter des analyses de logs pour lier les sessions.
**Mitigation** : Découplage technique total entre les tables d'identité et les tables de réponses anonymes. Absence de clés étrangères.
**Risque résiduel** : Comme pour tout système SaaS, la sécurité repose en dernier ressort sur les contrôles d'accès à l'infrastructure et la traçabilité des actions administrateur.
