
class VyConfigFileLine():
    def __init__(self, txt: str, idx: int):
        """VyConfigFileLine constructor

        Args:
            txt (str): text of line, stripped of trailing '\n'
            idx (int): index of line in a group of lines, one less than line-number

        Returns:
            VyConfigFileLine: constructed object
        """
        self.txt = txt
        self.idx = idx

    def __repr__(self) -> str:
        return repr((self.idx, self.txt))
