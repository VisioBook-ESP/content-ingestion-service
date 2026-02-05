class ProcessorFactory:
    def __init__(self, processors):
        self.processors = processors

    def get_processor(self, file_path: str):
        for p in self.processors:
            if p.can_handle(str(file_path)):
                return p
        raise Exception(f"Unsupported file type: {file_path}")
