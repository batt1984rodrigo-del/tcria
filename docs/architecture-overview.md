```mermaid
  graph TD;
    A[Client] --> B[API Server];
    B --> C[Database];
    B --> D[Cache];
    A <-- E[Authentication Service];
    E --> B;
```
