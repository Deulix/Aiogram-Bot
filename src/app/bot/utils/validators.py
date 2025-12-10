import aiohttp

from src.app.config.logger import logger
from src.app.config.settings import settings


async def validate_street_api(street: str) -> tuple[str, bool]:
    country = "Belarus"
    city = "Minsk"
    street_noralized = "улица " + " ".join(word.capitalize() for word in street.split())
    try:
        url = "https://geocode-maps.yandex.ru/v1"
        params = {
            "apikey": settings.MAPS_API_KEY,
            "geocode": f"{country}, {city}, {street}",
            "lang": "ru_RU",
            "results": 1,
            "format": "json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    geo_object = data["response"]["GeoObjectCollection"][
                        "featureMember"
                    ]
                    if geo_object:
                        geocoder_metadata = geo_object[0]["GeoObject"][
                            "metaDataProperty"
                        ]["GeocoderMetaData"]
                        precision = geocoder_metadata["precision"]
                        kind = geocoder_metadata["kind"]
                        if precision == kind == "street":
                            yandex_street_name = geo_object[0]["GeoObject"]["name"]
                            return yandex_street_name, True
                    return street_noralized, False
    except Exception as e:
        logger.error(e)
        return street_noralized, False
