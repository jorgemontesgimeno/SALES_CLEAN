#!/usr/bin/env python3
import argparse
import sys
import json
from pathlib import Path
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Filtra pedidos y genera un resumen de KPIs."
    )

    # === 4.1 Argumentos ===
    parser.add_argument("--input", required=True,
                        help="Ruta al CSV de pedidos (obligatorio).")

    parser.add_argument("--outdir", default="outputs",
                        help="Carpeta de salida (por defecto: outputs).")

    parser.add_argument("--start", type=str,
                        help="Fecha inicial para filtrar (YYYY-MM-DD).")

    parser.add_argument("--end", type=str,
                        help="Fecha final para filtrar (YYYY-MM-DD).")

    parser.add_argument("--country", type=str,
                        help="Filtrar por país (código o nombre).")

    parser.add_argument("--summary-format", choices=["txt", "json"],
                        default="txt", help="Formato del resumen (txt o json).")

    parser.add_argument("--export-filtered", action="store_true",
                        help="Guardar CSV con pedidos filtrados.")

    args = parser.parse_args()
    print("[INFO] Args:", args)  # TEMP: borra al finalizar

    # === 4.2 Validaciones y rutas ===
    in_path = Path(args.input)
    outdir = Path(args.outdir)

    if not in_path.exists():
        print(f"[ERROR] No existe el fichero: {in_path}", file=sys.stderr)
        sys.exit(1)

    outdir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] outdir listo en {outdir}")

    # === 4.3 Carga del CSV ===
    try:
        df = pd.read_csv(in_path, parse_dates=["date"])
    except Exception as e:
        print(f"[ERROR] Al leer CSV: {e}", file=sys.stderr)
        sys.exit(2)

    print("[INFO] filas cargadas:", df.shape[0])

    # === 4.4 Filtros opcionales ===
    if args.start:
        df = df[df["date"] >= pd.to_datetime(args.start)]
    if args.end:
        df = df[df["date"] <= pd.to_datetime(args.end)]
    if args.country:
        df = df[df["country"].str.upper() == args.country.upper()]

    print("[INFO] filas tras filtros:", df.shape[0])

    # === 4.5 Cálculo de KPIs ===
    def compute_kpis(df: pd.DataFrame) -> dict:
        """
        Aplica reglas acordadas en el Notebook:
        - Solo status == "paid"
        - num_orders, total_revenue, avg_order_value
        - Redondeo a 2 decimales cuando proceda
        """
        df_paid = df[df["status"] == "paid"].copy()
        num_orders = df_paid.shape[0]
        total_revenue = (df_paid["units"] * df_paid["unit_price"]).sum()
        avg_order_value = total_revenue / num_orders if num_orders > 0 else 0.0

        return {
            "num_orders": int(num_orders),
            "total_revenue": round(total_revenue, 2),
            "avg_order_value": round(avg_order_value, 2),
        }

    kpis = compute_kpis(df)
    print("[INFO] KPIs:", kpis)

    # === 4.6 Exportar resumen ===
    summary_path = None
    if args.summary_format == "txt":
        summary_path = outdir / "summary.txt"
        with summary_path.open("w", encoding="utf-8") as f:
            f.write("=== Sales Summary ===\n")
            f.write(f"Input: {in_path}\n")
            filtros = []
            if args.start:
                filtros.append(f"start={args.start}")
            if args.end:
                filtros.append(f"end={args.end}")
            if args.country:
                filtros.append(f"country={args.country}")
            if filtros:
                f.write("Filtros: " + ", ".join(filtros) + "\n")
            for k, v in kpis.items():
                f.write(f"{k}: {v}\n")
    else:
        summary_path = outdir / "summary.json"
        payload = {
            "input": str(in_path),
            "filters": {
                "start": args.start,
                "end": args.end,
                "country": args.country
            },
            "kpis": kpis
        }
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] Resumen guardado en {summary_path}")

    # === 4.7 Exportar pedidos filtrados (opcional) ===
    if args.export_filtered:
        filtered_path = outdir / "filtered.csv"
        df.to_csv(filtered_path, index=False, encoding="utf-8")
        print(f"[OK] Filtrado guardado en {filtered_path}")

    # === 4.8 Código de salida ===
    sys.exit(0)


if __name__ == "__main__":
    main()

