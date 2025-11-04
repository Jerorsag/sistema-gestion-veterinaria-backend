from datetime import date

class EstrategiaFIFO:
    def seleccionar_lote(self, lotes):
        return sorted(lotes, key=lambda l: l.fecha_ingreso)[0]

class EstrategiaFEFO:
    def seleccionar_lote(self, lotes):
        return sorted(lotes, key=lambda l: l.fecha_vencimiento or date.max)[0]
