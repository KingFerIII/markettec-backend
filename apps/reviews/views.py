from rest_framework import viewsets
from .models import Review
from .serializers import ReviewSerializer
from .permissions import IsReviewOwnerOrReadOnly
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['4. Reseñas'])
class ReviewViewSet(viewsets.ModelViewSet):
    """
    API Endpoint para Reseñas (Create, Edit, Delete, View).
    - Cualquiera (GET): Puede VER reseñas.
    - Usuario Logueado (POST): Puede CREAR una reseña.
    - Dueño (PUT/DELETE): Puede EDITAR o BORRAR su propia reseña.
    
    Para filtrar por producto, usa la URL:
    /api/reviews/?product_id=5
    """
    # OPTIMIZACIÓN #1: Definimos el queryset base con select_related
    # Esto evita el problema "N+1 Queries" al traer los datos del autor de golpe.
    queryset = Review.objects.select_related('reviewer', 'reviewer__user', 'product').all()
    
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewOwnerOrReadOnly]

    def get_queryset(self):
        """
        Filtra las reseñas por producto si se provee un 'product_id'
        en la URL (ej. /api/reviews/?product_id=5)
        """
        # Usamos el queryset optimizado definido arriba
        queryset = super().get_queryset()
        
        # Buscamos el parámetro 'product_id' en la URL
        product_id = self.request.query_params.get('product_id')
        
        if product_id is not None:
            # Filtramos el queryset para ese producto
            queryset = queryset.filter(product_id=product_id)
            
        return queryset

    def get_serializer_context(self):
        """ 
        Pasa el 'request' al serializer 
        (Necesario para que el serializer sepa quién es el autor 
        y para la validación de 'no-auto-reseña')
        """
        return {'request': self.request}