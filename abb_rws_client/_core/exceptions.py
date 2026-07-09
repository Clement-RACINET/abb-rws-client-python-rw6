# abb_rws_client/_core/exceptions.py
"""
Exceptions custom pour abb-rws6-python-client.

Hiérarchie :
    RWSError                        ← racine, toujours catchable en un seul except
    ├── RWSConnectionError          ← réseau inaccessible / timeout TCP
    ├── RWSTimeoutError             ← timeout HTTP dépassé
    ├── RWSAuthenticationError      ← 401 persistant après digest
    ├── RWSHTTPError                ← toute réponse HTTP >= 400 non couverte ci-dessus
    │   └── RWSNotFoundError        ← 404 (variable / ressource inexistante)
    ├── MastershipError             ← racine des erreurs mastership
    │   ├── MastershipDenied        ← contrôleur refuse l'acquisition
    │   └── MastershipNotHeld       ← tentative d'écriture sans mastership actif
    └── RWSValueError               ← valeur RAPID invalide / sérialisation échouée

CTRL_CODES :
    Dictionnaire complet des codes de retour ABB RobotWare 6.
    Source : robot_controller_return_code.xml (RWS API documentation).
    Clé   : code entier (positif = succès, négatif = erreur)
    Valeur : nom symbolique ABB (ex: "SYS_CTRL_E_MASTER_REJECT")
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Codes de retour ABB RobotWare 6 — source : return_codes.html
# Utilisés pour enrichir les messages d'erreur avec le nom symbolique ABB.
# ---------------------------------------------------------------------------

CTRL_CODES: dict[int, str] = {
    # ── Succès ──────────────────────────────────────────────────────────────
    294912:  "SYS_CTRL_S_OK",
    294913:  "SYS_CTRL_S_DONE",
    294914:  "SYS_CTRL_S_PENDING",
    294915:  "SYS_CTRL_S_GRANTED",
    294916:  "SYS_CTRL_S_NODATA_IN_EVENT",
    294917:  "SYS_CTRL_S_NO_CHANGE",
    294918:  "SYS_CTRL_S_NOT_VALID",
    294919:  "SYS_CTRL_E_ACCESS_TYPE",
    294920:  "SYS_CTRL_E_INVALID_HANDLE",
    299008:  "SYS_CTRL_S_RAPID_SYNTAX_ERROR",
    299009:  "SYS_CTRL_S_RAPID_SEMANTIC_ERROR",
    299010:  "SYS_CTRL_S_MECSTA_NOT_READY",
    299011:  "SYS_CTRL_S_RAPID_UNKNOWN_PROCEDURE",
    299012:  "SYS_CTRL_S_EVENT_ROUTINE_ABORTED",
    299013:  "SYS_CTRL_S_ABORTED",
    299014:  "SYS_CTRL_S_PREVIOUS_PATH_REMAINS",
    304129:  "SYS_CTRL_S_CFG_NAME_EXIST",
    # ── Erreurs générales ───────────────────────────────────────────────────
    -1073445887: "SYS_CTRL_E_OUTOFMEMORY",
    -1073445886: "SYS_CTRL_E_NOTIMPL",
    -1073445885: "SYS_CTRL_E_SERVICE_NOT_SUPPORTED",
    -1073445884: "SYS_CTRL_E_ACTIVE_SYSTEM",
    -1073445883: "SYS_CTRL_E_NO_DATA",
    -1073445882: "SYS_CTRL_E_DIR_NOT_COMPLETE",
    -1073445881: "SYS_CTRL_E_REJECT",
    -1073445880: "SYS_CTRL_E_RESOURCE_NOT_HELD",
    -1073445879: "SYS_CTRL_E_INVALIDARG",
    -1073445878: "SYS_CTRL_E_RESTORE_MISMATCH_CONTROLLER_ID",
    -1073445877: "SYS_CTRL_E_RESTORE_MISMATCH_KEY_ID",
    -1073445876: "SYS_CTRL_E_RESTORE_MISMATCH_ROBOT_TYPE",
    -1073445875: "SYS_CTRL_E_LOCAL_NOT_ALLOWED",
    -1073445873: "SYS_CTRL_E_NOT_LOGGED_ON",
    -1073445872: "SYS_CTRL_E_RESOURCE_ALREADY_HELD",
    -1073445871: "SYS_CTRL_E_MAX_LIMIT_REACHED",
    -1073445870: "SYS_CTRL_E_NO_SUCH_REQUEST",
    -1073445869: "SYS_CTRL_E_TIMEOUT",
    -1073445868: "SYS_CTRL_E_NO_LOCAL_USER",
    -1073445867: "SYS_CTRL_E_UAS_REJECT",
    -1073445866: "SYS_CTRL_E_UNRESOLVED_URL",
    -1073445865: "SYS_CTRL_E_BUFFER_OVERFLOW",
    -1073445863: "SYS_CTRL_E_DENIED",
    -1073445862: "SYS_CTRL_E_RESOURCE_HELD",
    -1073445861: "SYS_CTRL_E_FEATURE_DISABLED",
    -1073445860: "SYS_CTRL_E_MODE_REJECT",
    -1073445859: "SYS_CTRL_E_MASTER_REJECT",       # → MastershipDenied
    -1073445858: "SYS_CTRL_E_BACKUP_IN_PROGRESS",
    -1073445857: "SYS_CTRL_E_SYNC_STATE_REJECT",
    -1073445856: "SYS_CTRL_E_NOT_ACTIVE_REJECT",
    -1073445855: "SYS_CTRL_E_RESTORE_MISMATCH_SYSTEM_ID",
    -1073445854: "SYS_CTRL_E_RESTORE_MISMATCH_TEMPLATE_ID",
    -1073445853: "SYS_CTRL_E_INVALID_CID",
    -1073445852: "SYS_CTRL_E_TASK_SELECTION_PANEL_DISABLED",
    -1073445851: "SYS_CTRL_E_SYSFAIL_REJECT",
    -1073445850: "SYS_CTRL_E_SUBNET_MASK",
    -1073445849: "SYS_CTRL_E_IP_ADDRESS",
    -1073445848: "SYS_CTRL_E_IP_ADDRESS_DUPLICATE",
    -1073445847: "SYS_CTRL_E_NO_SUCH_CONDITION",
    -1073445846: "SYS_CTRL_E_PATH_STILL_ACTIVE",
    -1073445840: "SYS_CTRL_E_INVALIDSIZE",
    -1073445839: "SYS_CTRL_E_NAMEEXIST",
    -1073445838: "SYS_CTRL_E_INVALIDMSG",
    -1073445837: "SYS_CTRL_E_ABORTED",
    -1073445836: "SYS_CTRL_E_ALREADY_EXISTS",
    -1073445835: "SYS_CTRL_E_DEVICE_BUSY",
    -1073445834: "SYS_CTRL_E_GATEWAY_ADDRESS",
    -1073445833: "SYS_CTRL_E_NETWORK_CONFIGURATION",
    -1073445832: "SYS_CTRL_E_USER_HOOK_REJECT",
    # ── Erreurs RAPID ───────────────────────────────────────────────────────
    -1073442816: "SYS_CTRL_E_NO_SUCH_SYMBOL",       # → RWSNotFoundError
    -1073442815: "SYS_CTRL_E_SOURCEPOS",
    -1073442814: "SYS_CTRL_E_INVALID_PROGRAMFILE",
    -1073442813: "SYS_CTRL_E_MOD_AMBNAME",
    -1073442812: "SYS_CTRL_E_NO_PROGRAMNAME",
    -1073442811: "SYS_CTRL_E_MOD_READ_PROTECTED",
    -1073442810: "SYS_CTRL_E_MOD_WRITE_PROTECTED",
    -1073442809: "SYS_CTRL_E_EXEC_STATE",
    -1073442808: "SYS_CTRL_E_TASK_STATE",
    -1073442807: "SYS_CTRL_E_NOT_ON_PATH",
    -1073442806: "SYS_CTRL_E_EXEC_LEVEL",
    -1073442805: "SYS_CTRL_E_EXEC_CONTEXT_CONFLICT",
    -1073442804: "SYS_CTRL_E_RAPID_HEAP_FULL",
    -1073442803: "SYS_CTRL_E_RAPID_SYNTAX_ERROR",
    -1073442802: "SYS_CTRL_E_RAPID_SEMANTIC_ERROR",
    -1073442801: "SYS_CTRL_E_ILLEGAL_ENTRYPOINT",
    -1073442800: "SYS_CTRL_E_ILLEGAL_PCP_MOVE",
    -1073442799: "SYS_CTRL_E_MAX_ROBTARGETS_EXCEEDED",
    -1073442798: "SYS_CTRL_E_NOT_MODPOSSIBLE",
    -1073442797: "SYS_CTRL_E_ACTIVE_DISPLACEMENT",
    -1073442796: "SYS_CTRL_E_NOT_ON_PATH_CLEAR_DENIED",
    -1073442795: "SYS_CTRL_E_PREVIOUS_PATH_REMAINS",
    -1073442794: "SYS_CTRL_E_CHANGE_EXEC_MODE",
    -1073442793: "SYS_CTRL_E_EXEC_PAST_BEGINNING",
    -1073442792: "SYS_CTRL_E_ILLEGAL_TO_MOVE_PCP",
    -1073442791: "SYS_CTRL_E_TOO_MANY_USER_LEVELS",
    -1073442790: "SYS_CTRL_E_LAST_IN_CALL_CHAIN",
    -1073442789: "SYS_CTRL_E_START_ORDER_BREAK",
    -1073442788: "SYS_CTRL_E_CHANGE_EXEC_MODE_TASK_RUNNING",
    -1073442787: "SYS_CTRL_E_BACKWARD",
    -1073442786: "SYS_CTRL_E_SYMBOL_NOT_PERSISTENT",
    -1073442785: "SYS_CTRL_E_EXEC_STATE_BGTSK",
    -1073442784: "SYS_CTRL_E_UI_INSTRUCTION_NOT_ACTIVE",
    -1073442783: "SYS_CTRL_E_NO_PP",
    -1073442782: "SYS_CTRL_E_TOO_BIG_MODULE",
    # ── Erreurs fichier ─────────────────────────────────────────────────────
    -1073438720: "SYS_CTRL_E_GENERAL_FILE_ERROR",
    -1073438719: "SYS_CTRL_E_DEVICE_FULL",
    -1073438718: "SYS_CTRL_E_WRONG_DISK",
    -1073438717: "SYS_CTRL_E_DEVICE_NOT_READY",
    -1073438716: "SYS_CTRL_E_INVALID_PATH",
    -1073438715: "SYS_CTRL_E_NO_DEVICE",
    -1073438714: "SYS_CTRL_E_CREATE_DIRECTORY",
    -1073438713: "SYS_CTRL_E_DIR_NOT_EXIST",
    -1073438712: "SYS_CTRL_E_DIR_EXIST",
    -1073438711: "SYS_CTRL_E_DIR_NOT_EMPTY",
    -1073438709: "SYS_CTRL_E_CREATE_FILE",
    -1073438708: "SYS_CTRL_E_FILE_NOT_FOUND",
    -1073438707: "SYS_CTRL_E_FILENAME_TOO_LONG",
    -1073438706: "SYS_CTRL_E_NOT_ENOUGH_SPACE",
    -1073438705: "SYS_CTRL_E_PATH_TOO_LONG",
    # ── Erreurs IO ──────────────────────────────────────────────────────────
    -1073438208: "SYS_CTRL_E_IO_UNIT_DISABLE_NOT_ALLOWED",
    -1073438207: "SYS_CTRL_E_IO_UNIT_NOT_RUNNING",
    -1073438206: "SYS_CTRL_E_IO_UNBLOCKED_INSIGNAL",
    -1073438205: "SYS_CTRL_E_IO_CROSS_RESULTANT",
    -1073438204: "SYS_CTRL_E_IO_SET_BY_DEVICE_TRANSFER",
    # ── Erreurs CFG ─────────────────────────────────────────────────────────
    -1073437696: "SYS_CTRL_E_CFG_DOMAIN_INVALID",
    -1073437695: "SYS_CTRL_E_CFG_TYPE_INVALID",
    -1073437694: "SYS_CTRL_E_CFG_ATTRIBUTE_INVALID",
    -1073437693: "SYS_CTRL_E_CFG_ATTRIBUTE_OUT_OF_RANGE",
    -1073437691: "SYS_CTRL_E_CFG_INSTANCE_INVALID",
    -1073437689: "SYS_CTRL_E_CFG_NAME_EXIST",
    -1073437688: "SYS_CTRL_E_CFG_DATA_INCORRECT",
    -1073437687: "SYS_CTRL_E_CFG_STRING_ATTRIBUTE_LENGTH",
    -1073437686: "SYS_CTRL_E_CFG_VERSION",
    -1073437685: "SYS_CTRL_E_CS_NONEXISTENT",
    -1073437684: "SYS_CTRL_E_SS_NONEXISTENT",
    # ── Erreurs Motion ──────────────────────────────────────────────────────
    -1073436672: "SYS_CTRL_E_TOOL_ERROR",
    -1073436671: "SYS_CTRL_E_WOBJ_ERROR",
    -1073436670: "SYS_CTRL_E_MECHUNIT_DEACTIVATED",
    -1073436669: "SYS_CTRL_E_MECHPOS_NOT_IN_LIMIT",
    -1073436668: "SYS_CTRL_E_NO_SUCH_MECHUNIT",
    -1073436667: "SYS_CTRL_E_MECHUNIT_NOT_SINGLE",
    -1073436666: "SYS_CTRL_E_NO_TCPROBOT_ACTIVE",
    -1073436665: "SYS_CTRL_E_CALIB_NOT_FULL_RANK",
    -1073436664: "SYS_CTRL_E_CALIB_TOO_FEW_OR_TOO_MANY_TARGETS",
    -1073436663: "SYS_CTRL_E_CALIB_BAD_DISPL_RESULT",
    -1073436662: "SYS_CTRL_E_CALIB_COLLAPSED_PLANE",
    -1073436661: "SYS_CTRL_E_CALIB_COLLAPSED_NORMALIZATION",
    -1073436660: "SYS_CTRL_E_CALIB_ROBOT_TRACK_NOT_IMPLEMENTED",
    -1073436659: "SYS_CTRL_E_CALIB_UNDEFINED_FRAME_COORDINATION",
    -1073436658: "SYS_CTRL_E_POSE_X_AXIS_START_END_TOO_CLOSE",
    -1073436657: "SYS_CTRL_E_POSE_DEFINE_COLLAPSED",
    -1073436656: "SYS_CTRL_E_POSE_UNKNOWN_ORIGIN_SWITCH",
    -1073436655: "SYS_CTRL_E_POSE_DEFINE_POINTS_TOO_CLOSE",
    -1073436654: "SYS_CTRL_E_POSE_OUTSIDE_REACH",
    -1073436653: "SYS_CTRL_E_POSE_CONFIG_INCOMPATIBLE",
    -1073436652: "SYS_CTRL_E_HPJ_CHANGE_COUNT_MISMATCH",
    -1073436651: "SYS_CTRL_E_MECHUNIT_NOT_CONNECTED",
    -1073436650: "SYS_CTRL_E_MECSTA_NOT_READY",
    -1073436649: "SYS_CTRL_E_NME_ACTIVATION_ERROR",
    -1073436648: "SYS_CTRL_E_POSE_SINGULARITY",
    # ── Erreurs DIPC / Queue ────────────────────────────────────────────────
    -1073435904: "SYS_CTRL_E_INVALIDSLOTID",
    -1073435903: "SYS_CTRL_E_QUEUEFULL",
    -1073435902: "SYS_CTRL_E_POWER_FAIL_IN_PROGRESS",
    -1073435901: "SYS_CTRL_E_OPTION",
    -1073435900: "SYS_CTRL_E_INVALID_ID",
    -1073435899: "SYS_CTRL_E_NOT_VALIDATED",
    -1073435898: "SYS_CTRL_E_INVALID_DATA",
    -1073435897: "SYS_CTRL_E_SYNCHCHECK",
    -1073435896: "SYS_CTRL_E_CONFIGURATION_LOCKED",
    -1073435895: "SYS_CTRL_E_NOT_MANUAL_MODE",
    -1073435894: "SYS_CTRL_E_NOT_MOTORS_OFF",
    -1073435893: "SYS_CTRL_E_SC_COMMUNICATION_FAILED",
    -1073435892: "SYS_CTRL_E_SC_LOCK_INFO_MISMATCH",
    -1073435891: "SYS_CTRL_E_SERVICE_NOT_READY",
    -1073435890: "SYS_CTRL_E_ALREADY_IN_PROGRESS",
    -1073435889: "SYS_CTRL_E_OPERATION_IS_LOCKED",
    -1073435888: "SYS_CTRL_E_VERSION",
    -1073435887: "SYS_CTRL_E_INVALID_STATE",
    -1073435886: "SYS_CTRL_E_OPERATION_IS_UNLOCKED",
    -1073435885: "SYS_CTRL_E_INVALID_PIN_CODE",
    -1073435884: "SYS_CTRL_E_OPERATION_FAILED",
    # ── Erreurs génériques ──────────────────────────────────────────────────
    -1073414146: "SYS_CTRL_E_FAIL",
    -1073414145: "SYS_CTRL_E_UNEXPECTED",
}


def ctrl_code_name(code: int) -> str:
    """Retourne le nom symbolique ABB d'un code de retour, ou sa repr décimale.

    Args:
        code: Code entier retourné par le contrôleur ABB.

    Returns:
        Nom symbolique (ex: ``"SYS_CTRL_E_MASTER_REJECT"``) ou
        ``"UNKNOWN(code)"`` si le code n'est pas répertorié.

    Example:
        >>> ctrl_code_name(-1073445859)
        'SYS_CTRL_E_MASTER_REJECT'
        >>> ctrl_code_name(0)
        'UNKNOWN(0)'
    """
    return CTRL_CODES.get(code, f"UNKNOWN({code})")


# ---------------------------------------------------------------------------
# Racine
# ---------------------------------------------------------------------------


class RWSError(Exception):
    """Classe de base pour toutes les erreurs RWS.

    Attributes:
        message: Description lisible de l'erreur.
        status_code: Code HTTP associé, si applicable.
    """

    message: str
    status_code: int | None

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __repr__(self) -> str:
        if self.status_code is not None:
            return (
                f"{self.__class__.__name__}("
                f"message={self.message!r}, "
                f"status_code={self.status_code})"
            )
        return f"{self.__class__.__name__}(message={self.message!r})"


# ---------------------------------------------------------------------------
# Erreurs réseau / transport
# ---------------------------------------------------------------------------


class RWSConnectionError(RWSError):
    """Impossible d'établir la connexion TCP avec le contrôleur.

    Levée quand httpx.ConnectError ou httpx.ConnectTimeout est intercepté
    après épuisement de tous les retries.
    """


class RWSTimeoutError(RWSError):
    """Le contrôleur n'a pas répondu dans le délai imparti.

    Levée quand httpx.ReadTimeout ou httpx.PoolTimeout est intercepté
    après épuisement de tous les retries.
    """


# ---------------------------------------------------------------------------
# Erreurs HTTP
# ---------------------------------------------------------------------------


class RWSAuthenticationError(RWSError):
    """Authentification Digest refusée (401 persistant).

    Indique des credentials incorrects ou un utilisateur non autorisé
    dans l'UAS (User Authorization System) du contrôleur.
    """

    def __init__(self, message: str = "Authentication failed (HTTP 401)") -> None:
        super().__init__(message, status_code=401)


class RWSHTTPError(RWSError):
    """Réponse HTTP inattendue (>= 400) non couverte par une exception plus spécifique.

    Attributes:
        ctrl_code: Code de retour ABB extrait du corps de la réponse, si présent.
        ctrl_code_name: Nom symbolique ABB du code (ex: ``"SYS_CTRL_E_EXEC_STATE"``).
    """

    ctrl_code: int | None
    ctrl_code_name: str | None

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        ctrl_code: int | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code)
        self.ctrl_code = ctrl_code
        self.ctrl_code_name = ctrl_code_name(ctrl_code) if ctrl_code is not None else None

    def __repr__(self) -> str:
        parts = [f"message={self.message!r}"]
        if self.status_code is not None:
            parts.append(f"status_code={self.status_code}")
        if self.ctrl_code is not None:
            parts.append(f"ctrl_code={self.ctrl_code_name!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"


class RWSNotFoundError(RWSHTTPError):
    """Ressource RWS introuvable (HTTP 404).

    Typiquement : variable RAPID inexistante, module ou tâche incorrect.

    Attributes:
        resource: Chemin de la ressource introuvable.
    """

    resource: str

    def __init__(self, resource: str, ctrl_code: int | None = None) -> None:
        super().__init__(
            f"Resource not found: {resource}",
            status_code=404,
            ctrl_code=ctrl_code,
        )
        self.resource = resource


# ---------------------------------------------------------------------------
# Erreurs Mastership
# ---------------------------------------------------------------------------


class MastershipError(RWSError):
    """Classe de base pour les erreurs liées au mastership RAPID."""


class MastershipDenied(MastershipError):
    """Le contrôleur a refusé l'acquisition du mastership.

    Causes typiques :
    - Le programme RAPID tourne en mode automatique.
    - Un autre client détient déjà le mastership.
    - L'UAS refuse l'accès à cet utilisateur.

    Contrainte ABB : SYS_CTRL_E_MASTER_REJECT (code -1073445859).
    """

    def __init__(self, message: str = "Mastership request denied by controller") -> None:
        super().__init__(message, status_code=None)


class MastershipNotHeld(MastershipError):
    """Tentative d'opération d'écriture sans mastership actif.

    Levée côté client avant même d'envoyer la requête HTTP,
    comme garde-fou contre les appels mal ordonnés.
    """

    def __init__(self) -> None:
        super().__init__("Cannot write: mastership is not currently held")


# ---------------------------------------------------------------------------
# Erreurs de valeur / sérialisation
# ---------------------------------------------------------------------------


class RWSValueError(RWSError):
    """Valeur RAPID invalide ou échec de sérialisation / désérialisation.

    Levée par ``_core/serializers.py`` quand une valeur Python ne peut pas
    être convertie en format RWS, ou inversement.
    """
