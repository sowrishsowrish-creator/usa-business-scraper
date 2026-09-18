'''
Sowrish Sithanathan
Data Scraper
June 8 2026
GUI
'''
# tkinter and related GUI modules used throughout the application
# import tkinter as tk to reduce typing
import tkinter as tk

# for messagebox popups
from tkinter import messagebox

# for filedialog (save file picker)
from tkinter import filedialog

# for ttk styled widgets like buttons, labels, and entry fields
from tkinter import ttk

# import threading so the scrape doesnt freeze the GUI so the user can still interact with the app while it's running
import threading

# import files for organization; main runs everything, scraper does the scraping, exporter does the saving to export files
from scraper import BusinessScraper
from exporter import DataExporter


class ScraperApp:

    # ---- State Search Filter ----

    # filter the state list based on the search input and preserve currently selected entries
    def filterStates(self, *args):
        # called every time the user types in the state search box
        # filters the listbox to only show matching states

        search = self.stateSearchVar.get().lower()

        # remember which states are currently selected by name
        selectedNames = [self.listboxStates.get(i) for i in self.listboxStates.curselection()]

        # clear the listbox
        self.listboxStates.delete(0, tk.END)

        # re-insert only states that match the search text
        for state in self.allStates:
            if (search in state.lower()):
                self.listboxStates.insert(tk.END, state)

        # re-select any states that were previously selected and are still visible
        for i in range(self.listboxStates.size()):
            if (self.listboxStates.get(i) in selectedNames):
                self.listboxStates.selection_set(i)


    # ---- Scrape Controls ----

    # ---- Scrape Controls ----
    def startScrape(self):
        # validate inputs before starting
        # check that business types are provided
        if (not self.entryTypes.get()):
            self.setStatus("Business types cannot be blank.", "error")
            return
        # check that at least one state is selected
        if (not self.listboxStates.curselection()):
            self.setStatus("Please select at least one state.", "error")
            return

        # get business types (comma separated) and split into a list
        rawTypes = self.entryTypes.get()
        businessTypes = [t.strip() for t in rawTypes.split(",") if t.strip()]

        # get selected states from listbox
        selectedIndices = self.listboxStates.curselection()
        states = [self.listboxStates.get(i) for i in selectedIndices]

        # if every state is selected, use a single USA-wide query instead
        if (len(states) == len(self.allStates)):
            states = ["USA"]

        # disable the scrape button so user cant double-click
        self.btnScrape.config(state="disabled", text="Scraping...")
        self.setStatus("Opening Chrome and starting scrape...", "info")

        # run the scrape in a background thread so GUI stays responsive
        thread = threading.Thread(
            target=self.runScrapeThread,
            args=(businessTypes, states)
        )
        thread.daemon = True
        thread.start()


    # background scrape thread
    def runScrapeThread(self, businessTypes, states):
        # this runs in a background thread
        # creates a fresh scraper and runs it

        # wrapper callback that can handle confirmation requests from the scraper
        def scraper_callback(msg):
            # if the scraper sends a dict with confirm=True, show a yes/no popup
            if isinstance(msg, dict) and msg.get("confirm"):
                evt = threading.Event()
                result = {"answer": True}

                def ask():
                    answer = messagebox.askyesno("Continue?", msg.get("message", "Continue?"))
                    result["answer"] = answer
                    # also update status label with the same message
                    self.setStatus(msg.get("message", ""), "info")
                    evt.set()

                # schedule the popup on the main thread and wait for the user's response
                self.mainWin.after(0, ask)
                evt.wait()
                return result["answer"]

            # otherwise treat it as a normal status update
            text = msg if isinstance(msg, str) else str(msg)
            try:
                self.mainWin.after(0, lambda: self.setStatus(text, "info"))
            except Exception:
                pass
            return True

        self.scraper = BusinessScraper()
        self.scraper.scrapeAll(businessTypes, states, scraper_callback)

        # when done update the result count and re-enable button
        count = len(self.scraper.results)
        self.setStatus(f"Done!  {count} records found — ready to export.", "success")
        self.btnScrape.config(state="normal", text="Start Scrape")

        # update count badge and preview table
        self.countVar.set(f"{count} records found")
        self.updatePreview()


    # update the status label from the scraper thread
    def updateFeedback(self, msg):
        # safely update the status bar from any thread
        self.setStatus(msg, "info")


    # set the status message and color based on status type
    def setStatus(self, msg, statusType="info"):
        # updates the bottom status bar with color coding
        if (statusType == "success"):
            self.lblStatus.config(text=msg, fg="#2ecc71")
        elif (statusType == "error"):
            self.lblStatus.config(text=msg, fg="#e05555")
        else:
            self.lblStatus.config(text=msg, fg="#8a8fa8")


    # ---- Preview Table ----

    # ---- Preview Table ----
    def updatePreview(self):
        # clears and refills the treeview with all results

        # clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # insert all records
        for record in self.scraper.results:
            self.tree.insert("", tk.END, values=(
                record["Business Name"],
                record["Business Type"],
                record["Phone"],
                record["Email"],
                record["State"],
                record["Website"]
            ))


    # toggle select all / clear selection for the state listbox
    def selectAllStates(self):
        # clear any search filter and update the visible state list
        self.stateSearchVar.set("")
        totalStates = self.listboxStates.size()
        selectedCount = len(self.listboxStates.curselection())

        # select all if nothing or some states are selected, otherwise clear
        if (selectedCount == totalStates and totalStates > 0):
            self.listboxStates.selection_clear(0, tk.END)
        else:
            self.listboxStates.selection_set(0, tk.END)


    # ---- Export Controls ----

    # ---- Export Controls ----
    def exportCSV(self):
        # opens a save dialog and exports to CSV

        # check that there is data to export
        if (not self.scraper or not self.scraper.results):
            self.setStatus("Nothing to export. Run a scrape first.", "error")
            return
        
        # export data as a CSV file
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save as CSV"
        )
        # if it doesnt work, return
        if (not filepath):
            return

        # export the data
        answer = self.exporter.exportCSV(self.scraper.results, filepath)
        self.setStatus(answer, "success")


    # export the current results to an Excel file
    def exportExcel(self):
        # opens a save dialog and exports to Excel

        # check that there is data to export
        if (not self.scraper or not self.scraper.results):
            self.setStatus("Nothing to export. Run a scrape first.", "error")
            return

        # export data as an Excel file
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="Save as Excel"
        )

        if (not filepath):
            return

        answer = self.exporter.exportExcel(self.scraper.results, filepath)
        self.setStatus(answer, "success")


    # reset the application inputs and clear preview results
    def clearAll(self):
        # clears entries, listbox, preview, and resets everything

        self.entryTypes.delete(0, tk.END)
        self.listboxStates.selection_clear(0, tk.END)

        # also clear the state search box
        self.stateSearchVar.set("")

        # clear the scraper and count
        self.scraper = None
        self.countVar.set("No results yet")

        # clear the treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # shows the message on feedback once cleared
        self.setStatus("Cleared — ready for a new search.", "info")


    # ---- Menu Popups ----

    def exitWin(self):
        # exit with yes/no popup
        if (messagebox.askyesno("Exit", "Are you sure you want to exit?")):
            self.mainWin.destroy()


    # show the About popup dialog
    def aboutWin(self):
        messagebox.showinfo(
            "About",
            "USA Business Scraper\nScrapes Google for US small business contact info.\n\nExports to CSV or Excel."
        )


    # show the help / usage popup dialog
    def helpWin(self):
        messagebox.showinfo(
            "How To Use",
            "1. Enter business types separated by commas\n"
            "   Ex:  bakery, plumber, hair salon\n\n"
            "2. Search and select one or more states\n"
            "   Hold Cmd (Mac) to pick multiple\n\n"
            "3. Click Start Scrape\n"
            "   A Chrome window will open automatically\n\n"
            "4. When done, click Export CSV or Export Excel"
        )


    # show contact information popup dialog
    def contactMe(self):
        messagebox.showinfo(
        "Contact Me",
        "For questions or feedback, please open an issue on GitHub:\n\n"
        "github.com/sowrishsowrish-creator/usa-business-scraper/issues"
    )

    # ---- Init (builds the whole window) ----

    # initialize the main window, build all widgets, and launch the GUI loop
    def __init__(self):

        # create main window and configure theme, sizing, and title
        self.mainWin = tk.Tk()
        self.mainWin.title("USA Business Scraper")
        self.mainWin.configure(bg="#0f1117")

        # for full and half screen resizing
        self.mainWin.resizable(True, True)
        self.mainWin.minsize(800, 550)

        # start at a nice default size
        self.mainWin.geometry("1100x680")

        # scraper and exporter objects
        self.scraper  = None
        self.exporter = DataExporter()

        # count badge text
        self.countVar = tk.StringVar(value="No results yet")

        # state search variable - calling filterStates every time it changes
        self.stateSearchVar = tk.StringVar()
        self.stateSearchVar.trace_add("write", self.filterStates)

        # full list of all 50 states stored so filtering always works off the full list
        self.allStates = [
            "Alabama (AL)", "Alaska (AK)", "Arizona (AZ)", "Arkansas (AR)", "California (CA)",
            "Colorado (CO)", "Connecticut (CT)", "Delaware (DE)", "Florida (FL)", "Georgia (GA)",
            "Hawaii (HI)", "Idaho (ID)", "Illinois (IL)", "Indiana (IN)", "Iowa (IA)",
            "Kansas (KS)", "Kentucky (KY)", "Louisiana (LA)", "Maine (ME)", "Maryland (MD)",
            "Massachusetts (MA)", "Michigan (MI)", "Minnesota (MN)", "Mississippi (MS)", "Missouri (MO)",
            "Montana (MT)", "Nebraska (NE)", "Nevada (NV)", "New Hampshire (NH)", "New Jersey (NJ)",
            "New Mexico (NM)", "New York (NY)", "North Carolina (NC)", "North Dakota (ND)", "Ohio (OH)",
            "Oklahoma (OK)", "Oregon (OR)", "Pennsylvania (PA)", "Rhode Island (RI)", "South Carolina (SC)",
            "South Dakota (SD)", "Tennessee (TN)", "Texas (TX)", "Utah (UT)", "Vermont (VT)",
            "Virginia (VA)", "Washington (WA)", "West Virginia (WV)", "Wisconsin (WI)", "Wyoming (WY)"
        ]

        # ---- configure root grid to stretch ----
        self.mainWin.columnconfigure(0, weight=0)   # left panel fixed
        self.mainWin.columnconfigure(1, weight=1)   # right panel stretches
        self.mainWin.rowconfigure(0, weight=0)      # header fixed
        self.mainWin.rowconfigure(1, weight=1)      # content stretches
        self.mainWin.rowconfigure(2, weight=0)      # status bar fixed

        # ==== HEADER ====
        self.headerFrame = tk.Frame(
            self.mainWin,
            bg="#1c1f2e",
            height=60
        )
        self.headerFrame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.headerFrame.columnconfigure(0, weight=1)

        self.appTitle = tk.Label(
            self.headerFrame,
            text="Small Business Info Scraper",
            font=("Arial", 22, "bold"),
            fg="#f0f0f0",
            bg="#1c1f2e",
            pady=14
        )
        self.appTitle.grid(row=0, column=0, sticky="w", padx=24)


        # ==== LEFT PANEL (inputs + buttons) ====
        self.leftPanel = tk.Frame(
            self.mainWin,
            bg="#1c1f2e",
            width=270,
            padx=20,
            pady=20
        )
        self.leftPanel.grid(row=1, column=0, sticky="ns")
        self.leftPanel.grid_propagate(False)
        self.leftPanel.columnconfigure(0, weight=1)

        # -- Business Types section --
        tk.Label(
            self.leftPanel,
            text="BUSINESS TYPES",
            font=("Arial", 9, "bold"),
            fg="#8a8fa8",
            bg="#1c1f2e"
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        # entry box for the user to type business types
        self.entryTypes = tk.Entry(
            self.leftPanel,
            font=("Arial", 11),
            bg="#252836",
            fg="#f0f0f0",
            insertbackground="#f0f0f0",
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground="#ffffff",
            highlightcolor="#ffffff"
        )
        self.entryTypes.grid(row=1, column=0, sticky="ew", ipady=8, pady=(0, 4))

        # -- States section --
        tk.Label(
            self.leftPanel,
            text="SELECT STATES",
            font=("Arial", 9, "bold"),
            fg="#8a8fa8",
            bg="#1c1f2e"
        ).grid(row=3, column=0, sticky="w", pady=(0, 4))

        # state search box
        self.entryStateSearch = tk.Entry(
            self.leftPanel,
            textvariable=self.stateSearchVar,
            font=("Arial", 11),
            bg="#252836",
            fg="#f0f0f0",
            insertbackground="#f0f0f0",
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground="#ffffff",
            highlightcolor="#ffffff"
        )
        self.entryStateSearch.grid(row=4, column=0, sticky="ew", ipady=7, pady=(0, 4))

        searchRow = tk.Frame(self.leftPanel, bg="#1c1f2e")
        searchRow.grid(row=5, column=0, sticky="ew", pady=(0, 6))
        searchRow.columnconfigure(0, weight=1)

        tk.Label(
            searchRow,
            text="Search",
            font=("Arial", 9),
            fg="#8a8fa8",
            bg="#1c1f2e"
        ).grid(row=0, column=0, sticky="w")

        # button to quickly select or clear all visible states
        self.btnSelectAllStates = tk.Button(
            searchRow,
            text="All",
            font=("Arial", 9, "bold"),
            bg="black",
            fg="#8a8fa8",
            activebackground="black",
            activeforeground="#8a8fa8",
            padx=10,
            pady=4,
            bd=0,
            highlightthickness=0,
            relief="flat",
            command=self.selectAllStates
        )
        self.btnSelectAllStates.grid(row=0, column=1, sticky="e")

        # frame to hold listbox + scrollbar side by side
        stateFrame = tk.Frame(self.leftPanel, bg="#252836")
        stateFrame.grid(row=6, column=0, sticky="ew", pady=(0, 18))
        stateFrame.columnconfigure(0, weight=1)

        # listbox showing all US states for selection
        self.listboxStates = tk.Listbox(
            stateFrame,
            selectmode="multiple",
            font=("Arial", 10),
            bg="#252836",
            fg="#f0f0f0",
            selectbackground="#4f8ef7",
            selectforeground="#f0f0f0",
            activestyle="none",
            relief="flat",
            bd=0,
            height=11,
            exportselection=False,
            highlightthickness=0
        )
        self.listboxStates.grid(row=0, column=0, sticky="ew")

        stateScroll = tk.Scrollbar(
            stateFrame,
            command=self.listboxStates.yview,
            bg="#252836",
            troughcolor="#252836"
        )
        stateScroll.grid(row=0, column=1, sticky="ns")
        self.listboxStates.config(yscrollcommand=stateScroll.set)

        # populate listbox with all states to start
        for state in self.allStates:
            self.listboxStates.insert(tk.END, state)

        # -- Buttons --
        self.btnScrape = tk.Button(
            self.leftPanel,
            text="Start Scrape",
            font=("Arial", 12, "bold"),
            bg="black",
            fg="#8a8fa8",
            activebackground="black",
            activeforeground="#8a8fa8",
            pady=10,
            bd=0,
            highlightthickness=0,
            relief="flat",
            command=self.startScrape
        )
        self.btnScrape.grid(row=7, column=0, sticky="ew", pady=(0, 8))

        # export buttons side by side
        exportFrame = tk.Frame(self.leftPanel, bg="#1c1f2e")
        exportFrame.grid(row=8, column=0, sticky="ew", pady=(0, 8))
        exportFrame.columnconfigure(0, weight=1)
        exportFrame.columnconfigure(1, weight=1)

        # export results to CSV format
        self.btnCSV = tk.Button(
            exportFrame,
            text="Export CSV",
            font=("Arial", 12, "bold"),
            bg="black",
            fg="#8a8fa8",
            activebackground="black",
            activeforeground="#8a8fa8",
            pady=8,
            bd=0,
            highlightthickness=0,
            relief="flat",
            command=self.exportCSV
        )
        self.btnCSV.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        # export results to Excel format
        self.btnExcel = tk.Button(
            exportFrame,
            text="Export Excel",
            font=("Arial", 12, "bold"),
            bg="black",
            fg="#8a8fa8",
            activebackground="black",
            activeforeground="#8a8fa8",
            pady=8,
            bd=0,
            highlightthickness=0,
            relief="flat",
            command=self.exportExcel
        )
        self.btnExcel.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # clear all inputs and reset the app state
        self.btnClear = tk.Button(
            self.leftPanel,
            text="Clear",
            font=("Arial", 12, "bold"),
            bg="black",
            fg="#8a8fa8",
            activebackground="black",
            activeforeground="#8a8fa8",
            pady=8,
            bd=0,
            highlightthickness=0,
            relief="flat",
            command=self.clearAll
        )
        self.btnClear.grid(row=9, column=0, sticky="ew")

        # ==== RIGHT PANEL (results table) ====
        self.rightPanel = tk.Frame(
            self.mainWin,
            bg="#0f1117",
            padx=20,
            pady=20
        )
        self.rightPanel.grid(row=1, column=1, sticky="nsew")
        self.rightPanel.columnconfigure(0, weight=1)
        self.rightPanel.rowconfigure(1, weight=1)

        # results header row
        resultsHeader = tk.Frame(self.rightPanel, bg="#0f1117")
        resultsHeader.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        resultsHeader.columnconfigure(0, weight=1)

        tk.Label(
            resultsHeader,
            text="RESULTS PREVIEW",
            font=("Arial", 9, "bold"),
            fg="#8a8fa8",
            bg="#0f1117"
        ).grid(row=0, column=0, sticky="w")

        # count badge
        self.countLbl = tk.Label(
            resultsHeader,
            textvariable=self.countVar,
            font=("Arial", 9, "bold"),
            fg="#4f8ef7",
            bg="#0f1117"
        )
        self.countLbl.grid(row=0, column=1, sticky="e")

        # ---- Treeview (results table) ----
        treeFrame = tk.Frame(self.rightPanel, bg="#0f1117")
        treeFrame.grid(row=1, column=0, sticky="nsew")
        treeFrame.columnconfigure(0, weight=1)
        treeFrame.rowconfigure(0, weight=1)

        # style the treeview to match dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.Treeview",
            background="#252836",
            foreground="#f0f0f0",
            fieldbackground="#252836",
            rowheight=30,
            font=("Arial", 10)
        )
        style.configure(
            "Dark.Treeview.Heading",
            background="#1c1f2e",
            foreground="#8a8fa8",
            font=("Arial", 9, "bold"),
            relief="flat"
        )
        style.map(
            "Dark.Treeview",
            background=[("selected", "#4f8ef7")],
            foreground=[("selected", "#f0f0f0")]
        )

        # columns for the table
        cols = ("Business Name", "Type", "Phone", "Email", "State", "Website")

        # treeview widget used to display result rows
        self.tree = ttk.Treeview(
            treeFrame,
            columns=cols,
            show="headings",
            style="Dark.Treeview"
        )

        # set column headings and widths
        self.tree.heading("Business Name", text="Business Name")
        self.tree.heading("Type",          text="Type")
        self.tree.heading("Phone",         text="Phone")
        self.tree.heading("Email",         text="Email")
        self.tree.heading("State",         text="State")
        self.tree.heading("Website",       text="Website")

        self.tree.column("Business Name", width=200, minwidth=120)
        self.tree.column("Type",          width=110, minwidth=80)
        self.tree.column("Phone",         width=130, minwidth=100)
        self.tree.column("Email",         width=180, minwidth=120)
        self.tree.column("State",         width=100, minwidth=80)
        self.tree.column("Website",       width=200, minwidth=120)

        self.tree.grid(row=0, column=0, sticky="nsew")

        # scrollbar for the table
        treeScroll = ttk.Scrollbar(
            treeFrame,
            orient="vertical",
            command=self.tree.yview
        )
        treeScroll.grid(row=0, column=1, sticky="ns")
        self.tree.config(yscrollcommand=treeScroll.set)

        # ==== STATUS BAR ====
        self.statusBar = tk.Frame(
            self.mainWin,
            bg="#1c1f2e",
            height=32
        )
        self.statusBar.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.lblStatus = tk.Label(
            self.statusBar,
            text="Ready: enter business types and select a state to begin.",
            font=("Arial", 9),
            fg="#8a8fa8",
            bg="#1c1f2e",
            anchor="w",
            pady=6
        )
        self.lblStatus.pack(side="left", padx=16)

        # Menu Bar
        self.menuBar = tk.Menu(self.mainWin, bg="#1c1f2e", fg="#f0f0f0")
        self.mainWin.config(menu=self.menuBar)

        # menu bar file with specific command
        fileMenu = tk.Menu(self.menuBar, tearoff=0, bg="#1c1f2e", fg="#f0f0f0")
        fileMenu.add_command(label="Exit", command=self.exitWin)
        self.menuBar.add_cascade(label="File", menu=fileMenu)

        # action menu with button commands
        actionMenu = tk.Menu(self.menuBar, tearoff=0, bg="#1c1f2e", fg="#f0f0f0")
        actionMenu.add_command(label="Start Scrape", command=self.startScrape)
        actionMenu.add_command(label="Select All States", command=self.selectAllStates)
        actionMenu.add_separator()
        actionMenu.add_command(label="Export CSV",   command=self.exportCSV)
        actionMenu.add_command(label="Export Excel", command=self.exportExcel)
        actionMenu.add_command(label="Clear",        command=self.clearAll)
        self.menuBar.add_cascade(label="Actions", menu=actionMenu)

        # menu bar help with specific commands
        helpMenu = tk.Menu(self.menuBar, tearoff=0, bg="#1c1f2e", fg="#f0f0f0")
        helpMenu.add_command(label="How To Use", command=self.helpWin)
        helpMenu.add_command(label="About", command=self.aboutWin)
        helpMenu.add_command(label="Contact", command=self.contactMe)
        self.menuBar.add_cascade(label="Help", menu=helpMenu)

        # keep the window open
        self.mainWin.mainloop()
