from app.config import settings
from app.models.formatting import PricingDetailModel

class PricingEngine:
    @staticmethod
    def calculate_pricing(total_pages: int) -> PricingDetailModel:
        """
        Calculates pricing dynamically based on total formatted page count:
        - Base Fee: Up to 20 pages = 50.00 ETB
        - Incremental Fee: Pages > 20 = +1.50 ETB per page
        """
        base_fee = float(settings.BASE_FEE_ETB)
        threshold = int(settings.BASE_PAGE_THRESHOLD)
        per_page_rate = float(settings.INCREMENTAL_PER_PAGE_FEE_ETB)
        
        if total_pages <= threshold:
            incremental_fee = 0.0
            total_fee = base_fee
        else:
            extra_pages = total_pages - threshold
            incremental_fee = round(extra_pages * per_page_rate, 2)
            total_fee = round(base_fee + incremental_fee, 2)
            
        return PricingDetailModel(
            base_fee=base_fee,
            incremental_fee=incremental_fee,
            total_fee=total_fee,
            currency="ETB"
        )
