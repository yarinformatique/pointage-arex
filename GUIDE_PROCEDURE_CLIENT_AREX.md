# 📋 GUIDE OFFICIEL D'UTILISATION - PLATEFORME POINTAGE AREX
**Projet :** Pointage & Gestion des Présences par Badges QR Code  
**Chantier / Entreprise :** AREX - Génie Civil & BTP (Bobo-Dioulasso, Burkina Faso)  
**Éditeur Solution :** YAR INFORMATIQUE  

---

## 🎯 RÉPARTITION DES RÔLES
La plateforme fonctionne avec deux accès distincts selon le rôle de l'utilisateur :
1. **Le Promoteur / Pointeur sur le terrain :** Utilise son smartphone avec le lien **Scanner** (`.../scanner`).
2. **La Direction / Responsable RH :** Utilise son ordinateur ou sa tablette avec le lien **Tableau de Bord** (`.../`).

---

## PARTIE 1 : PROCÉDURE DU PROMOTEUR SUR LE CHANTIER (SMARTPHONE)

### Étape 1 : Connexion matinale
1. Le promoteur ouvre le lien reçu sur son smartphone (via WhatsApp ou navigateur) :  
   👉 `https://[VOTRE_LIEN]/scanner`
2. Le navigateur demande l'autorisation d'accéder à la caméra : appuyer sur **« Autoriser »**.
3. L'écran affiche directement la caméra de scan avec la bannière de phase en haut :
   - 🟢 **06h00 à 07h30** : Phase Arrivée À L'HEURE
   - 🟡 **07h30 à 09h00** : Phase Arrivée EN RETARD
   - 🔴 **Après 09h00** : Phase Arrivée HORS DÉLAI
   - 🔵 **À partir de 16h00** : Phase DESCENTE

---

### Étape 2 : Comment scanner le badge d'un ouvrier
1. L'ouvrier présente son badge QR devant l'objectif de la caméra (à environ 15 à 25 cm).
2. Dès que le QR code est détecté (moins de 0,5 seconde) :
   - Un **bip sonore** retentit.
   - Une **voix annonce** le nom de l'agent (ex: *« Bienvenue Laurent, à l'heure »*).
   - Un **grand badge de couleur** apparaît avec le matricule, le nom, la profession et l'heure exacte.
3. Le promoteur peut faire passer l'ouvrier suivant immédiatement.

---

### Étape 3 : Que faire en cas de situation particulière ?

| Situation rencontrée | Ce que dit / affiche l'écran | Action du promoteur |
| :--- | :--- | :--- |
| **Arrivée normale (06h00 - 07h30)** | 🟢 Badge Vert : **ARRIVÉE À L'HEURE** | Valider le passage de l'ouvrier sur le chantier. |
| **Arrivée tardive (07h30 - 09h00)** | 🟡 Badge Orange : **RETARD (+X min)** | Prévenir l'ouvrier que son retard est consigné. |
| **Arrivée tardive (> 09h00)** | 🔴 Badge Rouge : **HORS DÉLAI** | Demander la raison du retard majeur à consigner. |
| **Descente normale (dès 16h00)** | 🔵 Badge Bleu : **DESCENTE VALIDÉE** | Le temps de travail de la journée est calculé (ex: 8h45). L'ouvrier peut quitter le chantier. |
| **Descente tentée avant 16h00** | 🟡 **TROP TÔT (AVANT 16H)** | Bloqué : la descente n'est pas autorisée avant 16h00. |
| **⚠️ Tentative de descente sans scan du matin** | 🚨 **ALERTE SÉCURITÉ : Descente sans arrivée** | **Attention !** L'ouvrier n'a pas pointé ce matin. Le système sonne l'alarme et signale l'incident aux RH. L'ouvrier ne peut pas valider une journée complète frauduleusement. |
| **Double scan accidentel (< 60s)** | ℹ️ **DÉJÀ ENREGISTRÉ** | Pas d'inquiétude : le système ignore le double bip involontaire. |
| **Badge oublié ou QR abîmé** | 📷 Caméra ne lit pas | Taper simplement le matricule (ex: `Ag1`, `Ag15`) dans la case en bas et appuyer sur **« Valider »**. |
| **Manque de lumière / Nuit** | Visibilité sombre | Appuyer sur le bouton **« 🔦 Flash / Torche »** pour allumer la torche du smartphone. |

---

## PARTIE 2 : PROCÉDURE DE LA DIRECTION & RESSOURCES HUMAINES (PC / TABLETTE)

### Étape 1 : Accès au Tableau de Bord
1. Ouvrir le lien général sur l'ordinateur de la Direction :  
   👉 `https://[VOTRE_LIEN]/`
2. Vous accédez au panneau de contrôle complet en temps réel.

---

### Étape 2 : Suivi du chantier en direct
- **Les 8 compteurs en haut :**
  - Effectif Total (68)
  - Présents du jour
  - Ponctuels (À l'heure)
  - Retards constatés
  - Hors délai
  - Descentes effectuées
  - **Anomalies de sécurité (tentatives de triche ou descentes sans arrivée)**
  - Absents du jour
- **Bannière d'alerte rouge :** Si un ouvrier a tenté de badger à 16h sans être venu le matin, son nom et l'heure exacte sont affichés en tête de page.

---

### Étape 3 : Régularisation d'un pointage (En cas d'exception)
Si un ouvrier avait une autorisation spéciale de la Direction (mission extérieure, oubli exceptionnel) :
1. Dans le tableau du jour, chercher son nom ou matricule.
2. Cliquer sur le bouton gris **« Régulariser »**.
3. Saisir le **Code PIN Superviseur** (par défaut : `1234`).
4. Entrer l'heure d'arrivée réelle et le motif.
5. Valider : le registre est mis à jour proprement avec traçabilité.

---

### Étape 4 : Télécharger les rapports pour la paie et les réunions
1. **Rapport du jour :**
   - Cliquer sur le bouton vert **« 📥 Exporter Excel/CSV »**.
   - Vous obtenez un fichier Excel structuré avec les heures d'arrivée, de descente, le temps travaillé et le statut de chaque ouvrier.
2. **Synthèse mensuelle (Bilan pour la paie) :**
   - Aller dans l'onglet **« 📈 Synthèse Mensuelle »**.
   - Choisir le mois et l'année.
   - Visualiser le total d'heures, le nombre de retards, d'absences et le taux d'assiduité de chaque ouvrier.
   - Cliquer sur **« 📥 Exporter Synthèse Excel/CSV »** pour transmission à la comptabilité/paie.

---

### Étape 5 : Réimpression des badges QR Code
1. Aller dans l'onglet **« 🪪 Badges QR & Impression »**.
2. Tous les 68 badges de l'entreprise AREX s'affichent avec le logo, le matricule, le nom, le métier et le QR code officiel vectoriel.
3. Cliquer sur **« 🖨️ Imprimer la Planche de Badges (Format A4) »** pour imprimer et plastifier les badges.

---

## 🔒 CODES ET PARAMÈTRES PAR DÉFAUT
- **Code PIN Superviseur / Modification :** `1234` (modifiable dans l'onglet *Paramètres*)
- **Heure Arrivée Ponctuelle :** 06h00 à 07h30
- **Heure Retard :** 07h30 à 09h00
- **Heure Hors Délai :** Après 09h00
- **Heure Début Descente :** 16h00
- **Délai Anti-rebond :** 60 secondes

---
*Document rédigé par YAR INFORMATIQUE pour la Direction et les Collaborateurs du projet AREX.*
