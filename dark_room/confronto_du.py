# To run the script, enter the following in the terminal: runs, base_path, detector number, du number, and the x-axis range for histograms.
# Example: python3 comparison_du.py --runs "699,705,707,709" --base_path "/home/mariarita/root" --detector 192 --du "D0DU107CT" --xrange "650,690"

from ROOT import TFile, TH1D, TF1, TCanvas, TGraphErrors, TMultiGraph, gStyle, gApplication
import pandas as pd
import argparse
import os


def extract_histograms(file):
    histograms = []
    for key in file.GetListOfKeys():
        obj_name = key.GetName()
        obj = file.Get(obj_name)
        
        if isinstance(obj, TH1D):
            cloned_histograms = obj.Clone()  # Clone the histogram
            cloned_histograms.SetLineColor(1) 
            histograms.append(cloned_histograms)  
    return histograms


def extract_p1(file, dom_indices, p1_values, p1_errors, data_for_excel, run_number, pmt_type):
    for key in file.GetListOfKeys():
        obj_name = key.GetName()
        obj = file.Get(obj_name)
        
        if obj_name in ['META', 'h0', 'h1'] or not isinstance(obj, TH1D):
            continue

        functions = obj.GetListOfFunctions()
        for func in functions:
            if isinstance(func, TF1):
                p1 = func.GetParameter(1)
                p1_error = func.GetParError(1)
                dom_index = len(dom_indices)
                
                # Add data for Excel
                data_for_excel.append({
                    "Run": run_number,
                    "PMT_Type": pmt_type,
                    "DOM_Index": dom_index,
                    "P1": p1,
                    "P1_Error": p1_error
                })

                dom_indices.append(dom_index)
                p1_values.append(p1)
                p1_errors.append(p1_error)


def main(args):
    
    run_numbers = args.runs.split(",")  

    base_path = args.base_path
    detector_prefix = f"{args.detector:08d}"  
    du_name = args.du  

    file_extension_07 = f"__LASER_PATCHED_PMT07_L0.JPulsar.PMT07.root"
    file_extension_15 = f"__LASER_PATCHED_PMT15_L0.JPulsar.PMT15.root"
    
    data_for_excel = []

    output_dir = os.path.join(base_path, "dark_room", du_name, "laser", "fileoutput")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    xrange = list(map(float, args.xrange.split(',')))  # Convert range to a list of floats
    x_min, x_max = xrange[0], xrange[1]

    for ii, run_number in enumerate(run_numbers):
        
        file_name_07 = f"{base_path}/dark_room/{du_name}/laser/KM3NeT_{detector_prefix}_00000{run_number}{file_extension_07}"
        file_name_15 = f"{base_path}/dark_room/{du_name}/laser/KM3NeT_{detector_prefix}_00000{run_number}{file_extension_15}"
        
        file_07 = TFile(file_name_07, "READ")
        file_15 = TFile(file_name_15, "READ")
        
        histograms_07 = extract_histograms(file_07)
        histograms_15 = extract_histograms(file_15)

        dom_indices_07, p1_values_07, p1_errors_07 = [], [], []
        dom_indices_15, p1_values_15, p1_errors_15 = [], [], []
        
        extract_p1(file_07, dom_indices_07, p1_values_07, p1_errors_07, data_for_excel, run_number, "PMT07")
        extract_p1(file_15, dom_indices_15, p1_values_15, p1_errors_15, data_for_excel, run_number, "PMT15")

        n_points_07 = len(dom_indices_07)
        graph_07 = TGraphErrors(n_points_07)
        for i in range(n_points_07):
            graph_07.SetPoint(i, dom_indices_07[i], p1_values_07[i])
            graph_07.SetPointError(i, 0, p1_errors_07[i])
        graph_07.SetMarkerStyle(22)
        graph_07.SetMarkerColor(4)
        graph_07.SetMarkerSize(1.5)

        n_points_15 = len(dom_indices_15)
        graph_15 = TGraphErrors(n_points_15)
        for i in range(n_points_15):
            graph_15.SetPoint(i, dom_indices_15[i], p1_values_15[i])
            graph_15.SetPointError(i, 0, p1_errors_15[i])
        graph_15.SetMarkerStyle(21)
        graph_15.SetMarkerColor(2)
        graph_15.SetMarkerSize(1.5)
        
        graph_07.SetTitle(f"Run {run_number} {args.detector} PMT07")
        graph_15.SetTitle(f"Run {run_number} {args.detector} PMT15")

        canvas = TCanvas(f"canvas_{run_number}", f"Run {run_number} PMT07 + PMT15", 800, 600)
        multigraph = TMultiGraph()
        multigraph.Add(graph_07, "P")
        multigraph.Add(graph_15, "P")
        
        multigraph.SetTitle(f"Run {run_number}_DU107; DOM; laser hit time [ns]")
        multigraph.Draw("A")
        
        legend = canvas.BuildLegend(0.7, 0.7, 0.9, 0.9)
        legend.SetHeader(f"Run {run_number}", "C")
        legend.SetTextSize(0.03)

        canvas.SaveAs(f"{output_dir}/run_{run_number}_{args.detector}_PMT07_PMT15.png")
        print(f"Graph saved as {output_dir}/run_{run_number}_{args.detector}_PMT07_PMT15.png")

        canvas_07 = TCanvas(f"canvas_07_{run_number}", f"Run {run_number} PMT07", 1200, 800)
        canvas_07.Divide(6, 3) 
        
        canvas_07.cd()
        for i, hist_pmt07 in enumerate(histograms_07):
            canvas_07.cd(i + 1)  
            hist_pmt07.SetLineColor(1)  
            hist_pmt07.SetLineWidth(2)
            hist_pmt07.SetTitle(f"DOM {i} - PMT07")  
            hist_pmt07.Draw("HIST")  
            hist_pmt07.GetXaxis().SetRangeUser(x_min, x_max)
        
        canvas_07.SaveAs(f"{output_dir}/run_{run_number}_{args.detector}_PMT07_canvas.png")
        
        canvas_15 = TCanvas(f"canvas_15_{run_number}", f"Run {run_number} PMT15", 1200, 800)
        canvas_15.Divide(6, 3)  
        canvas_15.cd()

        for i, hist_pmt15 in enumerate(histograms_15):
            canvas_15.cd(i + 1) 
            hist_pmt15.SetLineColor(1)  
            hist_pmt15.SetLineWidth(2)
            hist_pmt15.SetTitle(f"DOM {i} - PMT15") 
            hist_pmt15.Draw("HIST")  
            hist_pmt15.GetXaxis().SetRangeUser(x_min, x_max)

        canvas_15.SaveAs(f"{output_dir}/run_{run_number}_{args.detector}_PMT15_canvas.png")
        print(f"Graphs saved for Run {run_number} in {output_dir}.")
        
        file_07.Close()
        file_15.Close()

    df = pd.DataFrame(data_for_excel)
    df.to_excel(f'{output_dir}/combined_{args.detector}_PMT07_PMT15.xlsx', index=False)
    print(f"Data saved in {output_dir}/combined_{args.detector}_PMT07_PMT15.xlsx")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate graphs for PMT07 and PMT15 from ROOT files.")
    parser.add_argument('--runs', type=str, required=True, help="Run numbers separated by commas (e.g. 699,705,707,709)")
    parser.add_argument('--base_path', type=str, required=True, help="Base path for ROOT files")
    parser.add_argument('--detector', type=int, required=True, help="Detector number (e.g. 192)")
    parser.add_argument('--du', type=str, required=True, help="DU name (e.g. D0DU107CT)")
    parser.add_argument('--xrange', type=str, required=True, help="X-axis range for histograms, format: min,max (e.g. 650,690)")

    args = parser.parse_args()
    main(args)
