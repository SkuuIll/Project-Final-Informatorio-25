import ClassicEditorBase from '@ckeditor/ckeditor5-editor-classic/src/classiceditor';

// Core plugins
import Essentials from '@ckeditor/ckeditor5-essentials/src/essentials';
import Autoformat from '@ckeditor/ckeditor5-autoformat/src/autoformat';
import PasteFromOffice from '@ckeditor/ckeditor5-paste-from-office/src/pastefromoffice';

// Basic styles
import Bold from '@ckeditor/ckeditor5-basic-styles/src/bold';
import Italic from '@ckeditor/ckeditor5-basic-styles/src/italic';
import Underline from '@ckeditor/ckeditor5-basic-styles/src/underline';
import Strikethrough from '@ckeditor/ckeditor5-basic-styles/src/strikethrough';
import Code from '@ckeditor/ckeditor5-basic-styles/src/code';
import Subscript from '@ckeditor/ckeditor5-basic-styles/src/subscript';
import Superscript from '@ckeditor/ckeditor5-basic-styles/src/superscript';

// Content structure
import Paragraph from '@ckeditor/ckeditor5-paragraph/src/paragraph';
import Heading from '@ckeditor/ckeditor5-heading/src/heading';
import BlockQuote from '@ckeditor/ckeditor5-block-quote/src/blockquote';
import List from '@ckeditor/ckeditor5-list/src/list';
import TodoList from '@ckeditor/ckeditor5-list/src/todolist';
import ListProperties from '@ckeditor/ckeditor5-list/src/listproperties';

// Links and media
import Link from '@ckeditor/ckeditor5-link/src/link';
import { LinkImage } from '@ckeditor/ckeditor5-link';
import Image from '@ckeditor/ckeditor5-image/src/image';
import ImageCaption from '@ckeditor/ckeditor5-image/src/imagecaption';
import ImageStyle from '@ckeditor/ckeditor5-image/src/imagestyle';
import ImageToolbar from '@ckeditor/ckeditor5-image/src/imagetoolbar';
import ImageResize from '@ckeditor/ckeditor5-image/src/imageresize';
import ImageInsert from '@ckeditor/ckeditor5-image/src/imageinsert';
import MediaEmbed from '@ckeditor/ckeditor5-media-embed/src/mediaembed';

// Tables
import Table from '@ckeditor/ckeditor5-table/src/table';
import TableToolbar from '@ckeditor/ckeditor5-table/src/tabletoolbar';
import { TableCaption } from '@ckeditor/ckeditor5-table';
import TableProperties from '@ckeditor/ckeditor5-table/src/tableproperties';
import TableCellProperties from '@ckeditor/ckeditor5-table/src/tablecellproperties';

// Formatting and layout
import Font from '@ckeditor/ckeditor5-font/src/font';
import Alignment from '@ckeditor/ckeditor5-alignment/src/alignment';
import Indent from '@ckeditor/ckeditor5-indent/src/indent';
import IndentBlock from '@ckeditor/ckeditor5-indent/src/indentblock';
import Highlight from '@ckeditor/ckeditor5-highlight/src/highlight';
import RemoveFormat from '@ckeditor/ckeditor5-remove-format/src/removeformat';

// Advanced features
import CodeBlock from '@ckeditor/ckeditor5-code-block/src/codeblock';
import SourceEditing from '@ckeditor/ckeditor5-source-editing/src/sourceediting';
import GeneralHtmlSupport from '@ckeditor/ckeditor5-html-support/src/generalhtmlsupport';
import { HtmlEmbed } from '@ckeditor/ckeditor5-html-embed';
import { FullPage } from '@ckeditor/ckeditor5-html-support';
import { Style } from '@ckeditor/ckeditor5-style';
import { HorizontalLine } from '@ckeditor/ckeditor5-horizontal-line';

// Special characters and mentions
import { SpecialCharacters } from '@ckeditor/ckeditor5-special-characters';
import { SpecialCharactersEssentials } from '@ckeditor/ckeditor5-special-characters';
import Mention from '@ckeditor/ckeditor5-mention/src/mention';

// Upload functionality
import UploadAdapter from '@ckeditor/ckeditor5-adapter-ckfinder/src/uploadadapter';
import SimpleUploadAdapter from '@ckeditor/ckeditor5-upload/src/adapters/simpleuploadadapter';
import { FileUploader } from '@liqd/ckeditor5-file-uploader';

// Utility features
import WordCount from '@ckeditor/ckeditor5-word-count/src/wordcount';
import { ShowBlocks } from '@ckeditor/ckeditor5-show-blocks';
import { SelectAll } from '@ckeditor/ckeditor5-select-all';
import { FindAndReplace } from '@ckeditor/ckeditor5-find-and-replace';
import FullScreen from '@pikulinpw/ckeditor5-fullscreen';

/**
 * Enhanced CKEditor 5 Classic Editor with optimized plugin loading
 * and better default configuration
 */
export default class ClassicEditor extends ClassicEditorBase {
    
    /**
     * Get default configuration for the editor
     */
    static getDefaultConfig() {
        return {
            toolbar: {
                items: [
                    'heading',
                    '|',
                    'bold',
                    'italic',
                    'underline',
                    'strikethrough',
                    'code',
                    'subscript',
                    'superscript',
                    '|',
                    'fontSize',
                    'fontFamily',
                    'fontColor',
                    'fontBackgroundColor',
                    'highlight',
                    '|',
                    'alignment',
                    'outdent',
                    'indent',
                    '|',
                    'numberedList',
                    'bulletedList',
                    'todoList',
                    '|',
                    'link',
                    'insertImage',
                    'insertTable',
                    'mediaEmbed',
                    'blockQuote',
                    'codeBlock',
                    'horizontalLine',
                    '|',
                    'specialCharacters',
                    'removeFormat',
                    '|',
                    'findAndReplace',
                    'selectAll',
                    'showBlocks',
                    'sourceEditing',
                    'fullScreen',
                    '|',
                    'undo',
                    'redo'
                ],
                shouldNotGroupWhenFull: true
            },
            
            heading: {
                options: [
                    { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' },
                    { model: 'heading1', view: 'h1', title: 'Heading 1', class: 'ck-heading_heading1' },
                    { model: 'heading2', view: 'h2', title: 'Heading 2', class: 'ck-heading_heading2' },
                    { model: 'heading3', view: 'h3', title: 'Heading 3', class: 'ck-heading_heading3' },
                    { model: 'heading4', view: 'h4', title: 'Heading 4', class: 'ck-heading_heading4' },
                    { model: 'heading5', view: 'h5', title: 'Heading 5', class: 'ck-heading_heading5' },
                    { model: 'heading6', view: 'h6', title: 'Heading 6', class: 'ck-heading_heading6' }
                ]
            },
            
            fontSize: {
                options: [
                    9, 10, 11, 12, 'default', 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72
                ]
            },
            
            fontFamily: {
                options: [
                    'default',
                    'Arial, Helvetica, sans-serif',
                    'Courier New, Courier, monospace',
                    'Georgia, serif',
                    'Lucida Sans Unicode, Lucida Grande, sans-serif',
                    'Tahoma, Geneva, sans-serif',
                    'Times New Roman, Times, serif',
                    'Trebuchet MS, Helvetica, sans-serif',
                    'Verdana, Geneva, sans-serif'
                ]
            },
            
            fontColor: {
                columns: 5,
                documentColors: 10,
                colorPicker: true
            },
            
            fontBackgroundColor: {
                columns: 5,
                documentColors: 10,
                colorPicker: true
            },
            
            image: {
                toolbar: [
                    'imageStyle:inline',
                    'imageStyle:block',
                    'imageStyle:side',
                    '|',
                    'toggleImageCaption',
                    'imageTextAlternative',
                    'linkImage',
                    '|',
                    'resizeImage'
                ],
                resizeOptions: [
                    {
                        name: 'resizeImage:original',
                        label: 'Original',
                        value: null
                    },
                    {
                        name: 'resizeImage:25',
                        label: '25%',
                        value: '25'
                    },
                    {
                        name: 'resizeImage:50',
                        label: '50%',
                        value: '50'
                    },
                    {
                        name: 'resizeImage:75',
                        label: '75%',
                        value: '75'
                    }
                ]
            },
            
            table: {
                contentToolbar: [
                    'tableColumn',
                    'tableRow',
                    'mergeTableCells',
                    'tableProperties',
                    'tableCellProperties',
                    'toggleTableCaption'
                ]
            },
            
            list: {
                properties: {
                    styles: true,
                    startIndex: true,
                    reversed: true
                }
            },
            
            htmlSupport: {
                allow: [
                    {
                        name: /.*/,
                        attributes: true,
                        classes: true,
                        styles: true
                    }
                ]
            },
            
            link: {
                decorators: {
                    openInNewTab: {
                        mode: 'manual',
                        label: 'Open in a new tab',
                        attributes: {
                            target: '_blank',
                            rel: 'noopener noreferrer'
                        }
                    }
                }
            },
            
            mention: {
                feeds: [
                    {
                        marker: '@',
                        feed: [],
                        minimumCharacters: 1
                    }
                ]
            },
            
            codeBlock: {
                languages: [
                    { language: 'plaintext', label: 'Plain text' },
                    { language: 'c', label: 'C' },
                    { language: 'cs', label: 'C#' },
                    { language: 'cpp', label: 'C++' },
                    { language: 'css', label: 'CSS' },
                    { language: 'diff', label: 'Diff' },
                    { language: 'html', label: 'HTML' },
                    { language: 'java', label: 'Java' },
                    { language: 'javascript', label: 'JavaScript' },
                    { language: 'php', label: 'PHP' },
                    { language: 'python', label: 'Python' },
                    { language: 'ruby', label: 'Ruby' },
                    { language: 'typescript', label: 'TypeScript' },
                    { language: 'xml', label: 'XML' }
                ]
            },
            
            mediaEmbed: {
                previewsInData: true
            },
            
            wordCount: {
                onUpdate: (stats) => {
                    // Custom word count update logic can be added here
                    console.log('Word count updated:', stats);
                }
            },
            
            // Performance optimizations
            typing: {
                transformations: {
                    remove: [
                        'enDash',
                        'emDash',
                        'oneHalf',
                        'oneThird',
                        'twoThirds',
                        'oneForth',
                        'threeQuarters'
                    ]
                }
            },
            
            // Accessibility improvements
            ui: {
                poweredBy: {
                    position: 'inside',
                    side: 'right',
                    label: 'This is a CKEditor 5 instance.'
                }
            },
            
            // Error handling
            initialData: '',
            
            // Placeholder text
            placeholder: 'Start typing...',
            
            // Language
            language: 'en'
        };
    }
    
    /**
     * Create editor with enhanced error handling and logging
     */
    static async create(sourceElementOrData, config = {}) {
        const finalConfig = {
            ...ClassicEditor.getDefaultConfig(),
            ...config
        };
        
        try {
            const editor = await super.create(sourceElementOrData, finalConfig);
            
            // Add error event listener
            editor.on('error', (eventInfo, data) => {
                console.error('CKEditor error:', data.error);
            });
            
            // Add ready event listener
            editor.on('ready', () => {
                console.log('CKEditor ready');
            });
            
            return editor;
            
        } catch (error) {
            console.error('Failed to create CKEditor instance:', error);
            throw error;
        }
    }
}

// Core plugins - always loaded
const corePlugins = [
    Essentials,
    Autoformat,
    PasteFromOffice,
    Paragraph,
    Bold,
    Italic,
    Link,
    List,
    Heading
];

// Optional plugins - loaded based on configuration
const optionalPlugins = [
    UploadAdapter,
    CodeBlock,
    Underline,
    Strikethrough,
    Code,
    Subscript,
    Superscript,
    BlockQuote,
    Image,
    ImageCaption,
    ImageStyle,
    ImageToolbar,
    ImageResize,
    Alignment,
    Font,
    SimpleUploadAdapter,
    MediaEmbed,
    RemoveFormat,
    Table,
    TableToolbar,
    TableCaption,
    TableProperties,
    TableCellProperties,
    Indent,
    IndentBlock,
    Highlight,
    TodoList,
    ListProperties,
    SourceEditing,
    GeneralHtmlSupport,
    ImageInsert,
    WordCount,
    Mention,
    Style,
    HorizontalLine,
    LinkImage,
    HtmlEmbed,
    FullPage,
    SpecialCharacters,
    SpecialCharactersEssentials,
    FileUploader,
    ShowBlocks,
    SelectAll,
    FindAndReplace,
    FullScreen
];

// Combine all plugins
ClassicEditor.builtinPlugins = [
    ...corePlugins,
    ...optionalPlugins
];

// Export plugin groups for selective loading
export { corePlugins, optionalPlugins };