class FolderbotError(Exception):
    def __init__(self, message):
        super(FolderbotError, self).__init__(message)


class NodeDoesNotExistError(FolderbotError):
    def __init__(self, filepath: str):
        message = f"No such file or folder: {filepath}"
        super(NodeDoesNotExistError, self).__init__(message)


class NodeExistsError(FolderbotError):
    def __init__(self, filepath: str):
        message = f"Already exists: {filepath}"
        super(NodeExistsError, self).__init__(message)


class NoAttachmentsInMessageError(FolderbotError):
    def __init__(self):
        message = f"Message did not contain any attachments"
        super(NoAttachmentsInMessageError, self).__init__(message)


class AttachmentsUploadFailedError(FolderbotError):
    def __init__(self, att_name: str):
        message = f"The attachment {att_name} failed to upload"
        super(AttachmentsUploadFailedError, self).__init__(message)


class CannotLsError(FolderbotError):
    def __init__(self, filepath: str):
        message = f"Cannot ls {filepath}: is not a directory"
        super(CannotLsError, self).__init__(message)


class CannotCdError(FolderbotError):
    def __init__(self, filepath: str):
        message = f"Cannot cd to {filepath}: is not a directory"
        super(CannotCdError, self).__init__(message)


class CdPreviousFromRootError(FolderbotError):
    def __init__(self):
        message = f"Cannot cd to previous directory from root"
        super(CdPreviousFromRootError, self).__init__(message)


class CreateNodeUnderFileError(FolderbotError):
    def __init__(self, name: str, filepath: str):
        message = f"Cannot create node {name} under {filepath}: is file"
        super(CreateNodeUnderFileError, self).__init__(message)


class NoPathsProvidedError(FolderbotError):
    def __init__(self, cmd: str):
        message = f"No paths provided for {cmd}"
        super(NoPathsProvidedError, self).__init__(message)


class CommandNotFoundError(FolderbotError):
    def __init__(self, cmd: str):
        message = f"Command not found: {cmd}"
        super(CommandNotFoundError, self).__init__(message)


class CannotRmRootError(FolderbotError):
    def __init__(self):
        message = f"Cannot remove root directory"
        super(CannotRmRootError, self).__init__(message)


class InvalidFilepathError(FolderbotError):
    def __init__(self, path: str, reason: str):
        message = f"Bad filepath {path} : {reason}"
        super(InvalidFilepathError, self).__init__(message)


if __name__ == '__main__': # pragma: no cover
    e = CdPreviousFromRootError()
    print(isinstance(e, CdPreviousFromRootError))