TABLE_STYLE = """
QTreeView {
    show-decoration-selected: 1;
}

QTreeView::item {
    /* border: 1px solid #d9d9d9; */
    border-top-color: transparent;
    border-bottom-color: transparent;
}

QTreeView::item:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
    /* border: 1px solid #bfcde4; */
}

QTreeView::branch:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
    /* border: 1px solid #bfcde4; */
}

QTreeView::branch:selected {
    /* border: 1px solid #6ea0f1; */
}

QTreeView::branch:selected:active{
    /* background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc); */
    color:black;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
}

QTreeView::branch:selected:!active {
    color:black;
    /* background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf); */
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
}

QTreeView::item:selected {
    /* border: 1px solid #6ea0f1; */
}

QTreeView::item:selected:active{
    /* background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc); */
    color:black;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
}

QTreeView::item:selected:!active {
    color:black;
    /* background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf); */
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
}


/* vline */
QTreeView::branch:has-siblings:!adjoins-item {
    border-image: url(':vline') 0;
}

/* branch-more */
QTreeView::branch:has-siblings:adjoins-item {
    border-image: url(':branch-more') 0;
}

/* branch-end */
QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image: url(':branch-end') 0;
}


/* branch-closed */
QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
        border-image: none;
        image: url(':add-circle-fill');
}

/* branch-open */
QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
        border-image: none;
        image: url(':indeterminate-circle-fill');
}
"""

DARK_TABLE_STYLE = """
QTreeView {
    show-decoration-selected: 1;
}

QTreeView::item {
    border-top-color: transparent;
    border-bottom-color: transparent;
}

QTreeView::item:hover {
    background-color: #636669;
    opacity: 0.1;
}

QTreeView::branch:hover {
    background-color: #636669;
    opacity: 0.1;
}

QTreeView::branch:selected:active{
    background-color: #636669;
    opacity: 0.1;
}

QTreeView::branch:selected:!active {
    background-color: #636669;
    opacity: 0.1;
}

QTreeView::item:selected:active{
    background-color: #636669;
    opacity: 0.1;
}

QTreeView::item:selected:!active {
    background-color: #636669;
    opacity: 0.1;
}

/* vline */
QTreeView::branch:has-siblings:!adjoins-item {
    border-image: url(':vline-white') 0;
}

/* branch-more */
QTreeView::branch:has-siblings:adjoins-item {
    border-image: url(':branch-more-white') 0;
}

/* branch-end */
QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image: url(':branch-end-white') 0;
}

/* branch-closed */
QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
        border-image: none;
        image: url(':add-circle-fill-white');
}

/* branch-open */
QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
        border-image: none;
        image: url(':indeterminate-circle-fill-white');
}
"""